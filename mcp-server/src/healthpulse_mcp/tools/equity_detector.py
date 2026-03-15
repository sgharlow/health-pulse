"""Equity detector tool — flags facilities in high social vulnerability index areas."""

import os
from typing import Any

from typing import Optional

from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_state


def _safe_float(value: Any) -> Optional[float]:
    """Convert value to float, return None on failure."""
    try:
        v = float(value)
        return round(v, 1)
    except (ValueError, TypeError):
        return None


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Detect equity gaps by correlating facility outcomes with county SVI scores.

    Args:
        domo: Authenticated DomoClient
        args: Tool arguments with keys:
            state (str, optional): Two-letter state code filter
            svi_threshold (float): SVI percentile threshold for high-vulnerability (default 0.75)
            outcome_measure (str): One of readmission|mortality|safety

    Returns:
        dict with equity_flags (top 20), disparity_summary, filters
    """
    community_id = os.environ.get("HP_COMMUNITY_DATASET_ID")
    facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID")

    if not community_id:
        return {
            "error": "HP_COMMUNITY_DATASET_ID environment variable not set",
            "note": (
                "The community SVI dataset has not been created yet. "
                "Load CDC Social Vulnerability Index data into Domo and set HP_COMMUNITY_DATASET_ID "
                "to enable equity analysis."
            ),
        }
    if not facilities_id:
        return {"error": "HP_FACILITIES_DATASET_ID environment variable not set"}

    state = validate_state(args.get("state"))
    svi_threshold = float(args.get("svi_threshold", 0.75))
    outcome_measure = args.get("outcome_measure", "readmission")

    # Build state condition
    state_condition = f"WHERE state = '{state}'" if state else ""

    # Query community SVI data (county level)
    try:
        svi_sql = (
            f"SELECT county_fips, county_name, state, svi_score, "
            f"poverty_rate, uninsured_rate, minority_pct, total_population "
            f"FROM table {state_condition}"
        )
        svi_rows = domo.query_as_dicts(community_id, svi_sql)
    except Exception as exc:
        return {"error": f"Community SVI query failed: {exc}"}

    # Build SVI lookup by county_fips — store full community data
    svi_by_fips: dict[str, dict[str, Any]] = {}
    for row in svi_rows:
        fips = str(row.get("county_fips", "") or "")
        try:
            score = float(row.get("svi_score", 0) or 0)
        except (ValueError, TypeError):
            score = 0.0
        if fips:
            svi_by_fips[fips] = {
                "svi_score": score,
                "poverty_rate": _safe_float(row.get("poverty_rate")),
                "uninsured_rate": _safe_float(row.get("uninsured_rate")),
                "minority_pct": _safe_float(row.get("minority_pct")),
                "total_population": _safe_float(row.get("total_population")),
                "county_name": row.get("county_name"),
            }

    # Query facilities with county_fips
    try:
        fac_sql = (
            f"SELECT facility_id, facility_name, state, county_fips, "
            f"hospital_overall_rating, hospital_type "
            f"FROM table {state_condition}"
        )
        fac_rows = domo.query_as_dicts(facilities_id, fac_sql)
    except Exception as exc:
        return {"error": f"Facilities query failed: {exc}"}

    # Join in Python: attach SVI score to each facility
    equity_flags: list[dict[str, Any]] = []
    high_svi_ratings: list[float] = []
    low_svi_ratings: list[float] = []

    for fac in fac_rows:
        fips = str(fac.get("county_fips", "") or "")
        community = svi_by_fips.get(fips)
        if community is None:
            fips_padded = fips.zfill(5)
            community = svi_by_fips.get(fips_padded)

        if community is None:
            continue

        svi_score = community["svi_score"]

        try:
            rating = float(fac.get("hospital_overall_rating", 0) or 0)
        except (ValueError, TypeError):
            rating = 0.0

        is_high_svi = svi_score >= svi_threshold
        if is_high_svi:
            high_svi_ratings.append(rating)
            equity_flags.append({
                "facility_id": fac.get("facility_id"),
                "facility_name": fac.get("facility_name"),
                "state": fac.get("state"),
                "county_fips": fips,
                "svi_score": round(svi_score, 4),
                "poverty_rate": community.get("poverty_rate"),
                "uninsured_rate": community.get("uninsured_rate"),
                "minority_pct": community.get("minority_pct"),
                "county_name": community.get("county_name"),
                "hospital_overall_rating": rating,
                "hospital_type": fac.get("hospital_type"),
                "outcome_measure": outcome_measure,
                "equity_flag": "high_vulnerability",
            })
        else:
            low_svi_ratings.append(rating)

    # Sort by SVI score descending (highest vulnerability first)
    equity_flags.sort(key=lambda x: x.get("svi_score", 0), reverse=True)

    # Compute disparity summary
    avg_high = (sum(high_svi_ratings) / len(high_svi_ratings)) if high_svi_ratings else None
    avg_low = (sum(low_svi_ratings) / len(low_svi_ratings)) if low_svi_ratings else None

    disparity_summary: dict[str, Any] = {
        "high_svi_facility_count": len(high_svi_ratings),
        "low_svi_facility_count": len(low_svi_ratings),
        "avg_star_rating_high_svi": round(avg_high, 2) if avg_high is not None else None,
        "avg_star_rating_low_svi": round(avg_low, 2) if avg_low is not None else None,
        "rating_gap": (
            round(avg_low - avg_high, 2)
            if avg_high is not None and avg_low is not None
            else None
        ),
    }

    return {
        "equity_flags": equity_flags[:20],
        "disparity_summary": disparity_summary,
        "filters": {
            "state": state,
            "svi_threshold": svi_threshold,
            "outcome_measure": outcome_measure,
        },
        "clinical_context": {
            "what_svi_means": (
                "CDC Social Vulnerability Index (SVI) ranges 0-1. Higher values indicate "
                "greater community vulnerability to health threats. SVI >= 0.75 indicates "
                "the most vulnerable 25% of communities."
            ),
            "equity_implications": (
                "Facilities serving high-SVI communities often face resource constraints, "
                "higher uninsured rates, and social determinants that affect health outcomes "
                "independently of clinical care quality."
            ),
            "data_source": (
                "CDC/ATSDR Social Vulnerability Index 2022, based on US Census Bureau "
                "American Community Survey data."
            ),
        },
    }
