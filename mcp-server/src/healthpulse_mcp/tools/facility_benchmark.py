"""Facility benchmark tool — compares specific facilities across quality and readmission metrics."""

import os
from typing import Any

from healthpulse_mcp.domo_client import DomoClient


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

    facility_ids: list[str] = args.get("facility_ids", [])
    measures: list[str] = args.get("measures", [])

    if not facility_ids:
        return {"error": "facility_ids is required and must be non-empty"}

    # Build IN clause for facility IDs
    ids_quoted = ", ".join(f"'{fid}'" for fid in facility_ids)
    fac_where = f"WHERE facility_id IN ({ids_quoted})"

    # Query facilities
    try:
        fac_sql = (
            f"SELECT facility_id, facility_name, state, city, zip_code, "
            f"hospital_type, overall_rating, emergency_services "
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
            "city": row.get("city"),
            "zip_code": row.get("zip_code"),
            "hospital_type": row.get("hospital_type"),
            "overall_rating": row.get("overall_rating"),
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
                "city": None,
                "zip_code": None,
                "hospital_type": None,
                "overall_rating": None,
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
        quality_sql = (
            f"SELECT facility_id, measure_id, score, compared_to_national, footnote "
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
                "score": row.get("score"),
                "compared_to_national": row.get("compared_to_national"),
                "footnote": row.get("footnote"),
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
    }
