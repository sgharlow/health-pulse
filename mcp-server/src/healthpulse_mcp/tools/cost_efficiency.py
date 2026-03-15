"""Cost efficiency tool — analyzes Medicare spending per beneficiary by facility."""

import os
from typing import Any, Optional

from healthpulse_mcp.cache import TOOL_TTL, tool_cache
from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_state


def _safe_float(value: Any) -> Optional[float]:
    """Convert value to float, return None on failure."""
    try:
        v = float(value)
        return round(v, 4)
    except (ValueError, TypeError):
        return None


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Analyze Medicare spending efficiency across facilities.

    Args:
        domo: Authenticated DomoClient
        args: Tool arguments with keys:
            state (str, optional): Two-letter state code filter
            spending_threshold (float): Ratio threshold for overspending (default 1.1)
            limit (int): Max overspenders to return (default 20)

    Returns:
        dict with summary, overspenders, cost_quality_correlation, clinical_context, filters
    """
    # --- Cache check ---
    cache_key = tool_cache.make_key("cost_efficiency", args)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    cost_id = os.environ.get("HP_COST_DATASET_ID")
    facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID")

    if not cost_id:
        return {
            "error": "HP_COST_DATASET_ID environment variable not set",
            "note": (
                "The Medicare spending per beneficiary dataset has not been configured. "
                "Load CMS MSPB data into Domo and set HP_COST_DATASET_ID to enable "
                "cost efficiency analysis."
            ),
        }
    if not facilities_id:
        return {"error": "HP_FACILITIES_DATASET_ID environment variable not set"}

    state = validate_state(args.get("state"))
    spending_threshold = float(args.get("spending_threshold", 1.1))
    limit = min(int(args.get("limit", 20)), 100)

    # Build state condition for cost query (cost dataset has state column)
    state_condition = f"WHERE state = '{state}'" if state else ""

    # Query cost efficiency data — the score column IS the spending ratio
    # (hospital spending / national average). 1.0 = national avg, >1.0 = overspending.
    try:
        cost_sql = (
            f"SELECT facility_id, facility_name, state, score "
            f"FROM table {state_condition}"
        )
        cost_rows = domo.query_as_dicts(cost_id, cost_sql)
    except Exception as exc:
        return {"error": f"Cost efficiency query failed: {exc}"}

    # Query facilities for star ratings (hospital_overall_rating) for cost-quality correlation
    fac_state_condition = f"WHERE state = '{state}'" if state else ""
    try:
        fac_sql = (
            f"SELECT facility_id, hospital_overall_rating "
            f"FROM table {fac_state_condition}"
        )
        fac_rows = domo.query_as_dicts(facilities_id, fac_sql)
    except Exception as exc:
        return {"error": f"Facilities query failed: {exc}"}

    # Build star rating lookup by facility_id
    star_by_id: dict[str, Any] = {}
    for fac in fac_rows:
        fid = str(fac.get("facility_id", "") or "")
        if fid:
            star_by_id[fid] = fac.get("hospital_overall_rating")

    # Compute spending ratios and classify
    all_ratios: list[float] = []
    overspenders: list[dict[str, Any]] = []
    highest_ratio = 0.0
    highest_facility = ""

    # Cost-quality correlation counters
    high_cost_low_quality = 0
    high_cost_high_quality = 0
    low_cost_low_quality = 0
    low_cost_high_quality = 0

    for row in cost_rows:
        fid = str(row.get("facility_id", "") or "")
        if not fid:
            continue

        # The score column is already the spending ratio
        ratio = _safe_float(row.get("score"))
        if ratio is None:
            continue

        all_ratios.append(ratio)

        # Get facility info from the cost dataset itself
        fac_name = row.get("facility_name", "Unknown") or "Unknown"
        fac_state = row.get("state", "Unknown") or "Unknown"

        # Get star rating from the facilities dataset
        star_rating_raw = star_by_id.get(fid)

        # Parse star rating
        try:
            star_rating_num = float(star_rating_raw) if star_rating_raw else None
        except (ValueError, TypeError):
            star_rating_num = None

        # Track highest spending ratio
        if ratio > highest_ratio:
            highest_ratio = ratio
            highest_facility = fac_name

        # Classify cost vs quality
        is_high_cost = ratio > spending_threshold
        is_high_quality = star_rating_num is not None and star_rating_num >= 4
        is_low_quality = star_rating_num is not None and star_rating_num <= 2

        if is_high_cost and is_low_quality:
            high_cost_low_quality += 1
        elif is_high_cost and is_high_quality:
            high_cost_high_quality += 1
        elif not is_high_cost and is_low_quality:
            low_cost_low_quality += 1
        elif not is_high_cost and is_high_quality:
            low_cost_high_quality += 1

        # Build cost-quality flag
        cost_quality_flag = None
        if is_high_cost and is_low_quality:
            cost_quality_flag = "high cost, low quality"
        elif is_high_cost and is_high_quality:
            cost_quality_flag = "high cost, high quality"
        elif not is_high_cost and is_low_quality:
            cost_quality_flag = "low cost, low quality"
        elif not is_high_cost and is_high_quality:
            cost_quality_flag = "low cost, high quality"

        if is_high_cost:
            overspenders.append({
                "facility_id": fid,
                "facility_name": fac_name,
                "state": fac_state,
                "spending_ratio": ratio,
                "star_rating": str(star_rating_raw) if star_rating_raw else "N/A",
                "cost_quality_flag": cost_quality_flag,
            })

    # Sort overspenders by ratio descending
    overspenders.sort(key=lambda x: x.get("spending_ratio", 0), reverse=True)

    total_analyzed = len(all_ratios)
    overspending_count = len(overspenders)
    avg_ratio = round(sum(all_ratios) / len(all_ratios), 4) if all_ratios else 0.0
    overspending_pct = round((overspending_count / total_analyzed) * 100, 2) if total_analyzed > 0 else 0.0

    # Cost-quality correlation insight
    if overspending_count > 0 and high_cost_low_quality > 0:
        pct_inefficient = round((high_cost_low_quality / overspending_count) * 100, 1)
        insight = (
            f"{pct_inefficient}% of overspending facilities also have below-average star ratings, "
            f"suggesting potential inefficiency"
        )
    elif overspending_count > 0:
        insight = (
            "No overspending facilities have below-average star ratings in this dataset, "
            "suggesting higher spending may be associated with higher quality"
        )
    else:
        insight = "No overspending facilities identified at the given threshold"

    result = {
        "total_facilities_analyzed": total_analyzed,
        "summary": {
            "avg_spending_ratio": avg_ratio,
            "overspending_count": overspending_count,
            "overspending_pct": overspending_pct,
            "highest_spending_facility": highest_facility,
            "highest_spending_ratio": highest_ratio,
        },
        "overspenders": overspenders[:limit],
        "cost_quality_correlation": {
            "high_cost_low_quality": high_cost_low_quality,
            "high_cost_high_quality": high_cost_high_quality,
            "low_cost_low_quality": low_cost_low_quality,
            "low_cost_high_quality": low_cost_high_quality,
            "insight": insight,
        },
        "clinical_context": {
            "about_mspb": (
                "Medicare Spending Per Beneficiary (MSPB) measures Medicare Part A and B "
                "spending during an episode of care that starts 3 days prior to a hospital "
                "admission and extends 30 days post-discharge. It includes all Medicare-covered "
                "services during this window."
            ),
            "why_it_matters": (
                "MSPB is used in CMS Value-Based Purchasing to assess hospital cost efficiency. "
                "Higher spending does not correlate with better outcomes. Facilities with high "
                "spending ratios and low quality ratings represent the clearest opportunities "
                "for value improvement."
            ),
        },
        "filters": {
            "state": state,
            "spending_threshold": spending_threshold,
            "limit": limit,
        },
    }

    tool_cache.set(cache_key, result, TOOL_TTL)
    return result
