"""Facility benchmark tool — compares specific facilities across quality and readmission metrics."""

import os
from typing import Any

from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_facility_ids


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Benchmark specific facilities against each other.

    Args:
        domo: Authenticated DomoClient
        args: Tool arguments with keys:
            facility_ids (list[str]): Required list of facility IDs to compare
            measures (list[str], optional): Specific measure IDs to include

    Returns:
        dict with facilities (list with nested measures), comparison_count
    """
    facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID")
    quality_id = os.environ.get("HP_QUALITY_DATASET_ID")
    readmissions_id = os.environ.get("HP_READMISSIONS_DATASET_ID")

    if not facilities_id:
        return {"error": "HP_FACILITIES_DATASET_ID environment variable not set"}
    if not quality_id:
        return {"error": "HP_QUALITY_DATASET_ID environment variable not set"}
    if not readmissions_id:
        return {"error": "HP_READMISSIONS_DATASET_ID environment variable not set"}

    facility_ids: list[str] = validate_facility_ids(args.get("facility_ids", []))
    measures: list[str] = args.get("measures", [])

    if not facility_ids:
        return {"error": "facility_ids is required and must be non-empty"}

    # Build IN clause for facility IDs
    ids_quoted = ", ".join(f"'{fid}'" for fid in facility_ids)
    fac_where = f"WHERE facility_id IN ({ids_quoted})"

    # Query facilities — actual column names: city_town, hospital_overall_rating
    try:
        fac_sql = (
            f"SELECT facility_id, facility_name, state, city_town, zip_code, "
            f"hospital_type, hospital_overall_rating, emergency_services "
            f"FROM table {fac_where}"
        )
        fac_rows = domo.query_as_dicts(facilities_id, fac_sql)
    except Exception as exc:
        return {"error": f"Facilities query failed: {exc}"}

    # Build facility lookup
    facilities_map: dict[str, dict[str, Any]] = {}
    for row in fac_rows:
        fid = str(row.get("facility_id", ""))
        facilities_map[fid] = {
            "facility_id": fid,
            "facility_name": row.get("facility_name"),
            "state": row.get("state"),
            "city_town": row.get("city_town"),
            "zip_code": row.get("zip_code"),
            "hospital_type": row.get("hospital_type"),
            "hospital_overall_rating": row.get("hospital_overall_rating"),
            "emergency_services": row.get("emergency_services"),
            "quality_measures": [],
            "readmission_measures": [],
        }

    # Also include any requested facility IDs not found in facilities dataset
    for fid in facility_ids:
        if fid not in facilities_map:
            facilities_map[fid] = {
                "facility_id": fid,
                "facility_name": None,
                "state": None,
                "city_town": None,
                "zip_code": None,
                "hospital_type": None,
                "hospital_overall_rating": None,
                "emergency_services": None,
                "quality_measures": [],
                "readmission_measures": [],
                "note": "Facility not found in facilities dataset",
            }

    # Query quality measures for these facilities
    try:
        quality_conditions = [f"facility_id IN ({ids_quoted})"]
        if measures:
            meas_quoted = ", ".join(f"'{m}'" for m in measures)
            quality_conditions.append(f"measure_id IN ({meas_quoted})")
        q_where = f"WHERE {' AND '.join(quality_conditions)}"
        # Quality dataset columns: facility_id, measure_id, measure_name, score, compared_to_national
        quality_sql = (
            f"SELECT facility_id, measure_id, measure_name, score, compared_to_national "
            f"FROM table {q_where}"
        )
        quality_rows = domo.query_as_dicts(quality_id, quality_sql)
    except Exception as exc:
        return {"error": f"Quality query failed: {exc}"}

    for row in quality_rows:
        fid = str(row.get("facility_id", ""))
        if fid in facilities_map:
            facilities_map[fid]["quality_measures"].append({
                "measure_id": row.get("measure_id"),
                "measure_name": row.get("measure_name"),
                "score": row.get("score"),
                "compared_to_national": row.get("compared_to_national"),
            })

    # Query readmission measures for these facilities
    try:
        readm_conditions = [f"facility_id IN ({ids_quoted})"]
        if measures:
            meas_quoted = ", ".join(f"'{m}'" for m in measures)
            readm_conditions.append(f"measure_id IN ({meas_quoted})")
        r_where = f"WHERE {' AND '.join(readm_conditions)}"
        readm_sql = (
            f"SELECT facility_id, measure_id, excess_readmission_ratio, "
            f"predicted_readmission_rate, expected_readmission_rate, "
            f"number_of_readmissions "
            f"FROM table {r_where}"
        )
        readm_rows = domo.query_as_dicts(readmissions_id, readm_sql)
    except Exception as exc:
        return {"error": f"Readmissions query failed: {exc}"}

    for row in readm_rows:
        fid = str(row.get("facility_id", ""))
        if fid in facilities_map:
            facilities_map[fid]["readmission_measures"].append({
                "measure_id": row.get("measure_id"),
                "excess_readmission_ratio": row.get("excess_readmission_ratio"),
                "predicted_rate": row.get("predicted_readmission_rate"),
                "expected_rate": row.get("expected_readmission_rate"),
                "number_of_readmissions": row.get("number_of_readmissions"),
            })

    # Return in the order the caller provided
    ordered_facilities = [
        facilities_map[fid] for fid in facility_ids if fid in facilities_map
    ]

    return {
        "facilities": ordered_facilities,
        "comparison_count": len(ordered_facilities),
        "clinical_context": {
            "how_to_compare": (
                "Compare quality_measures.score values across facilities for the same "
                "measure_id. For mortality measures, lower scores are better. "
                "For process measures (SEP_1, IMM_3), higher scores are better."
            ),
            "star_rating_guide": (
                "CMS Overall Hospital Quality Star Ratings range 1-5. Based on 46+ measures "
                "across mortality, safety, readmission, patient experience, and timeliness. "
                "Fewer than 30% of US hospitals earn a 5-star rating."
            ),
            "readmission_interpretation": (
                "excess_readmission_ratio > 1.0 means more readmissions than predicted "
                "after adjusting for patient mix. CMS uses this for the Hospital Readmissions "
                "Reduction Program (HRRP) payment adjustments."
            ),
        },
    }
