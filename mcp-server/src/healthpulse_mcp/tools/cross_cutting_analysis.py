"""Cross-cutting analysis — finds multi-dimensional patterns across quality, equity, and care gaps."""

import os
from typing import Any

from healthpulse_mcp.cache import TOOL_TTL, tool_cache
from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_state


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Find facilities with MULTIPLE simultaneous concerns (quality + equity + readmissions).

    This is the tool that demonstrates AI's unique value — connecting dots across
    siloed data sources to identify systemic failures that individual metrics miss.
    """
    # --- Cache check ---
    cache_key = tool_cache.make_key("cross_cutting_analysis", args)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    state = validate_state(args.get("state"))

    fac_id = os.environ.get("HP_FACILITIES_DATASET_ID", "")
    qual_id = os.environ.get("HP_QUALITY_DATASET_ID", "")
    readm_id = os.environ.get("HP_READMISSIONS_DATASET_ID", "")
    com_id = os.environ.get("HP_COMMUNITY_DATASET_ID", "")

    if not all([fac_id, qual_id, readm_id]):
        return {"error": "Required dataset IDs not configured"}

    # Get facilities
    fac_where = f"WHERE state = '{state}'" if state else ""
    facilities = domo.query_as_dicts(fac_id,
        f"SELECT facility_id, facility_name, state, hospital_overall_rating, county_fips "
        f"FROM table {fac_where}")
    fac_lookup = {f["facility_id"]: f for f in facilities}
    fac_ids = set(f["facility_id"] for f in facilities)

    # Get quality flags (worse than national)
    qual_rows = domo.query_as_dicts(qual_id,
        "SELECT facility_id, measure_id, score, compared_to_national FROM table "
        "WHERE compared_to_national = 'Worse Than the National Rate'")
    qual_rows = [r for r in qual_rows if r["facility_id"] in fac_ids]

    quality_flags: dict[str, list[str]] = {}
    for r in qual_rows:
        fid = r["facility_id"]
        quality_flags.setdefault(fid, []).append(r.get("measure_id", ""))

    # Get readmission gaps
    readm_where = f"WHERE state = '{state}'" if state else ""
    readm_rows = domo.query_as_dicts(readm_id,
        f"SELECT facility_id, measure_name, excess_readmission_ratio "
        f"FROM table {readm_where}")

    readmission_gaps: dict[str, list[dict]] = {}
    for r in readm_rows:
        try:
            ratio = float(r.get("excess_readmission_ratio", 0) or 0)
        except (ValueError, TypeError):
            continue
        if ratio > 1.05:
            fid = r["facility_id"]
            readmission_gaps.setdefault(fid, []).append({
                "measure": r.get("measure_name", ""),
                "excess_ratio": round(ratio, 3),
            })

    # Get SVI data
    svi_by_fips: dict[str, dict] = {}
    if com_id:
        svi_where = f"WHERE state = '{state}'" if state else ""
        svi_rows = domo.query_as_dicts(com_id,
            f"SELECT county_fips, svi_score, poverty_rate, uninsured_rate, minority_pct "
            f"FROM table {svi_where}")
        for r in svi_rows:
            fips = str(r.get("county_fips", ""))
            try:
                svi_by_fips[fips] = {
                    "svi_score": float(r.get("svi_score", 0) or 0),
                    "poverty_rate": float(r.get("poverty_rate", 0) or 0),
                    "uninsured_rate": float(r.get("uninsured_rate", 0) or 0),
                    "minority_pct": float(r.get("minority_pct", 0) or 0),
                }
            except (ValueError, TypeError):
                pass

    # Cross-cutting: find facilities with MULTIPLE concerns
    multi_concern = []
    for fid, fac in fac_lookup.items():
        concerns = []
        concern_count = 0

        # Check quality
        q_flags = quality_flags.get(fid, [])
        if len(q_flags) >= 2:
            concerns.append(
                f"Worse than national on {len(q_flags)} quality measures: "
                f"{', '.join(q_flags[:3])}"
            )
            concern_count += 1

        # Check readmissions
        r_gaps = readmission_gaps.get(fid, [])
        if r_gaps:
            worst = max(r_gaps, key=lambda x: x["excess_ratio"])
            concerns.append(
                f"Excess readmissions ({len(r_gaps)} conditions), worst: "
                f"{worst['measure']} at {worst['excess_ratio']}x"
            )
            concern_count += 1

        # Check equity/SVI
        county_fips = str(fac.get("county_fips", ""))
        svi_data = svi_by_fips.get(county_fips) or svi_by_fips.get(county_fips.zfill(5))
        if svi_data and svi_data["svi_score"] >= 0.75:
            concerns.append(
                f"Serves high-vulnerability community (SVI={svi_data['svi_score']:.2f}, "
                f"poverty={svi_data['poverty_rate']:.1f}%, "
                f"uninsured={svi_data['uninsured_rate']:.1f}%)"
            )
            concern_count += 1

        # Check star rating
        try:
            rating = float(fac.get("hospital_overall_rating", 0) or 0)
        except (ValueError, TypeError):
            rating = 0
        if rating > 0 and rating <= 2:
            concerns.append(f"Low CMS star rating: {int(rating)} of 5")
            concern_count += 1

        if concern_count >= 2:
            multi_concern.append({
                "facility_id": fid,
                "facility_name": fac.get("facility_name", ""),
                "state": fac.get("state", ""),
                "star_rating": rating if rating > 0 else "N/A",
                "concern_count": concern_count,
                "concerns": concerns,
                "svi_data": svi_data,
            })

    multi_concern.sort(key=lambda x: x["concern_count"], reverse=True)

    # Systemic pattern detection
    patterns = []
    if multi_concern:
        svi_overlap = sum(
            1 for m in multi_concern
            if m.get("svi_data") and m["svi_data"]["svi_score"] >= 0.75
        )
        if svi_overlap > len(multi_concern) * 0.5:
            patterns.append(
                f"{svi_overlap} of {len(multi_concern)} multi-concern facilities "
                f"({svi_overlap * 100 // len(multi_concern)}%) serve high-vulnerability "
                f"communities — suggesting systemic equity-driven quality gaps"
            )

        low_rated = sum(
            1 for m in multi_concern
            if isinstance(m.get("star_rating"), (int, float)) and m["star_rating"] <= 2
        )
        if low_rated > 3:
            patterns.append(
                f"{low_rated} multi-concern facilities have 1-2 star CMS ratings — "
                f"these require coordinated intervention across quality, readmissions, "
                f"and community health"
            )

    result = {
        "multi_concern_facilities": multi_concern[:15],
        "total_multi_concern": len(multi_concern),
        "total_facilities_analyzed": len(facilities),
        "systemic_patterns": patterns,
        "filters": {"state": state},
        "clinical_context": {
            "why_cross_cutting_matters": (
                "Individual quality metrics viewed in isolation miss systemic failures. "
                "A hospital with high readmissions AND serving a high-poverty community "
                "AND rated 1-star has fundamentally different needs than one with just "
                "high readmissions. Cross-cutting analysis identifies these compounding "
                "risk factors."
            ),
            "action_required": (
                "Multi-concern facilities should be prioritized for comprehensive quality "
                "improvement programs that address clinical care, community partnerships, "
                "and resource allocation simultaneously."
            ),
        },
    }

    tool_cache.set(cache_key, result, TOOL_TTL)
    return result
