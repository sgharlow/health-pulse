"""Care gap finder tool — identifies facilities with excess readmission ratios or worse-than-national mortality."""

import os
from typing import Any

from healthpulse_mcp.cache import TOOL_TTL, tool_cache
from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_state

GAP_TYPE_SOURCES = {
    "readmission": ["readmissions"],
    "mortality": ["quality"],
    "safety": ["quality"],
    "all": ["readmissions", "quality"],
}


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Find facilities with care gaps (excess readmissions or worse-than-national quality).

    Args:
        domo: Authenticated DomoClient
        args: Tool arguments with keys:
            state (str, optional): Two-letter state code filter
            gap_type (str): One of readmission|mortality|safety|all
            min_excess_ratio (float): Minimum excess readmission ratio to flag (default 1.05)

    Returns:
        dict with gaps (top 30), total_gaps, filters
    """
    # --- Cache check ---
    cache_key = tool_cache.make_key("care_gap_finder", args)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    readmissions_id = os.environ.get("HP_READMISSIONS_DATASET_ID")
    quality_id = os.environ.get("HP_QUALITY_DATASET_ID")

    state = validate_state(args.get("state"))
    gap_type = args.get("gap_type", "all")
    min_excess_ratio = float(args.get("min_excess_ratio", 1.05))

    sources = GAP_TYPE_SOURCES.get(gap_type, ["readmissions", "quality"])

    # Build WHERE clause for datasets that have a 'state' column (readmissions, facilities)
    conditions = []
    if state:
        conditions.append(f"state = '{state}'")
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    gaps: list[dict[str, Any]] = []

    # Query readmissions dataset for excess ratios
    if "readmissions" in sources:
        if not readmissions_id:
            return {"error": "HP_READMISSIONS_DATASET_ID environment variable not set"}
        try:
            sql = (
                f"SELECT facility_id, facility_name, state, measure_id, "
                f"excess_readmission_ratio, number_of_readmissions, predicted_readmission_rate "
                f"FROM table {where_clause}"
            )
            rows = domo.query_as_dicts(readmissions_id, sql)
            for row in rows:
                try:
                    ratio = float(row.get("excess_readmission_ratio", 0) or 0)
                except (ValueError, TypeError):
                    continue
                if ratio >= min_excess_ratio:
                    gaps.append({
                        "source": "readmission",
                        "gap_type": "excess_readmission",
                        "facility_id": row.get("facility_id"),
                        "facility_name": row.get("facility_name"),
                        "state": row.get("state"),
                        "measure_id": row.get("measure_id"),
                        "excess_ratio": round(ratio, 4),
                        "number_of_readmissions": row.get("number_of_readmissions"),
                        "predicted_rate": row.get("predicted_readmission_rate"),
                    })
        except Exception as exc:
            return {"error": f"Readmissions query failed: {exc}"}

    # Query quality dataset for "Worse Than the National Rate" mortality/safety.
    # Quality dataset has NO 'state' column — when state is provided, first fetch
    # facility_ids from the facilities dataset, then filter quality data in Python.
    if "quality" in sources:
        if not quality_id:
            return {"error": "HP_QUALITY_DATASET_ID environment variable not set"}

        # Resolve facility_ids for state filtering (same pattern as quality_monitor.py)
        quality_facility_ids: set[str] | None = None
        if state:
            facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID")
            if not facilities_id:
                return {
                    "error": (
                        "HP_FACILITIES_DATASET_ID environment variable not set "
                        "(required for state filter on quality data)"
                    )
                }
            try:
                fac_sql = f"SELECT facility_id FROM table WHERE state = '{state}'"
                fac_rows = domo.query_as_dicts(facilities_id, fac_sql)
                quality_facility_ids = {str(r.get("facility_id")) for r in fac_rows}
            except Exception as exc:
                return {"error": f"Facilities query failed: {exc}"}

        try:
            # Filter by measure prefix depending on gap_type — no state condition here
            measure_conditions: list[str] = []
            if gap_type == "mortality":
                measure_conditions.append("measure_id LIKE 'MORT_%'")
            elif gap_type == "safety":
                measure_conditions.append(
                    "(measure_id LIKE 'PSI_%' OR measure_id LIKE 'HAI_%' OR measure_id LIKE 'COMP_%')"
                )
            elif gap_type == "all":
                measure_conditions.append(
                    "(measure_id LIKE 'MORT_%' OR measure_id LIKE 'PSI_%' OR "
                    "measure_id LIKE 'HAI_%' OR measure_id LIKE 'COMP_%')"
                )

            q_where = f"WHERE {' AND '.join(measure_conditions)}" if measure_conditions else ""
            # Quality dataset only has facility_id (no facility_name or state)
            sql = (
                f"SELECT facility_id, measure_id, compared_to_national, score "
                f"FROM table {q_where}"
            )
            rows = domo.query_as_dicts(quality_id, sql)

            # Apply state filter in Python when needed
            if quality_facility_ids is not None:
                rows = [r for r in rows if str(r.get("facility_id")) in quality_facility_ids]

            for row in rows:
                compared = str(row.get("compared_to_national", "") or "")
                if "Worse" in compared:
                    # Use score as excess_ratio proxy (score / national avg not available, so set 1.0)
                    try:
                        score = float(row.get("score", 0) or 0)
                    except (ValueError, TypeError):
                        score = 0.0
                    gaps.append({
                        "source": "quality",
                        "gap_type": "worse_than_national",
                        "facility_id": row.get("facility_id"),
                        "facility_name": None,
                        "state": None,
                        "measure_id": row.get("measure_id"),
                        "excess_ratio": 1.0,
                        "compared_to_national": compared,
                        "score": score,
                    })
        except Exception as exc:
            return {"error": f"Quality query failed: {exc}"}

    # Sort by excess_ratio descending
    gaps.sort(key=lambda x: x.get("excess_ratio", 0), reverse=True)

    result = {
        "gaps": gaps[:30],
        "total_gaps": len(gaps),
        "filters": {
            "state": state,
            "gap_type": gap_type,
            "min_excess_ratio": min_excess_ratio,
        },
        "clinical_context": {
            "what_excess_ratio_means": (
                "An excess readmission ratio > 1.0 means the hospital readmits more patients "
                "than expected. 1.10 = 10% more readmissions than predicted. "
                "CMS penalizes hospitals with high ratios."
            ),
            "financial_impact": (
                "CMS reduces payments by up to 3% for hospitals with excess readmissions. "
                "Total Medicare readmission costs: ~$26 billion/year."
            ),
        },
    }

    tool_cache.set(cache_key, result, TOOL_TTL)
    return result
