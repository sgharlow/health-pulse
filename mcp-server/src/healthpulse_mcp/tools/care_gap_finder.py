"""Care gap finder tool — identifies facilities with excess readmission ratios or worse-than-national mortality."""

import os
from typing import Any

from healthpulse_mcp.domo_client import DomoClient

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
    readmissions_id = os.environ.get("HP_READMISSIONS_DATASET_ID")
    quality_id = os.environ.get("HP_QUALITY_DATASET_ID")

    state = args.get("state")
    gap_type = args.get("gap_type", "all")
    min_excess_ratio = float(args.get("min_excess_ratio", 1.05))

    sources = GAP_TYPE_SOURCES.get(gap_type, ["readmissions", "quality"])

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

    # Query quality dataset for "Worse Than the National Rate" mortality/safety
    if "quality" in sources:
        if not quality_id:
            return {"error": "HP_QUALITY_DATASET_ID environment variable not set"}
        try:
            # Filter by measure prefix depending on gap_type
            measure_conditions = list(conditions)
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

    return {
        "gaps": gaps[:30],
        "total_gaps": len(gaps),
        "filters": {
            "state": state,
            "gap_type": gap_type,
            "min_excess_ratio": min_excess_ratio,
        },
    }
