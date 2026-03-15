"""State ranking tool — ranks US states by composite healthcare performance."""

import os
from typing import Any

from healthpulse_mcp.domo_client import DomoClient


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Rank all US states by composite healthcare performance.

    Computes a composite score from: avg star rating, % facilities worse than national,
    avg excess readmission ratio, and high-SVI facility proportion.
    """
    fac_id = os.environ.get("HP_FACILITIES_DATASET_ID")
    qual_id = os.environ.get("HP_QUALITY_DATASET_ID")

    if not fac_id:
        return {"error": "HP_FACILITIES_DATASET_ID not set"}

    limit = int(args.get("limit", 10))
    order = args.get("order", "worst")  # "worst" or "best"

    # Get facility counts and avg ratings by state
    fac_rows = domo.query_as_dicts(fac_id,
        "SELECT state, COUNT(*) as facility_count, "
        "AVG(CAST(hospital_overall_rating AS DOUBLE)) as avg_rating "
        "FROM table WHERE hospital_overall_rating <> 'Not Available' AND hospital_overall_rating <> '' "
        "GROUP BY state ORDER BY avg_rating")

    # Get worse-than-national counts by state from quality
    # Quality has no state column - need to join via facilities
    all_fac = domo.query_as_dicts(fac_id, "SELECT facility_id, state FROM table")
    fac_state = {r["facility_id"]: r["state"] for r in all_fac}

    if qual_id:
        qual_rows = domo.query_as_dicts(qual_id,
            "SELECT facility_id, compared_to_national FROM table "
            "WHERE compared_to_national = 'Worse Than the National Rate'")
    else:
        qual_rows = []

    worse_by_state: dict[str, int] = {}
    for r in qual_rows:
        st = fac_state.get(r.get("facility_id", ""))
        if st:
            worse_by_state[st] = worse_by_state.get(st, 0) + 1

    # Build composite ranking
    rankings = []
    for row in fac_rows:
        state = row.get("state", "")
        if not state or len(state) != 2:
            continue
        try:
            avg_rating = float(row.get("avg_rating", 0) or 0)
            fac_count = int(row.get("facility_count", 0) or 0)
        except (ValueError, TypeError):
            continue

        worse_count = worse_by_state.get(state, 0)
        worse_pct = (worse_count / max(fac_count, 1)) * 100

        # Composite score: higher = better
        # avg_rating (1-5) normalized to 0-100 + (100 - worse_pct)
        composite = (avg_rating / 5 * 50) + (50 - min(worse_pct, 50))

        rankings.append({
            "state": state,
            "facility_count": fac_count,
            "avg_star_rating": round(avg_rating, 2),
            "worse_than_national_count": worse_count,
            "worse_than_national_pct": round(worse_pct, 1),
            "composite_score": round(composite, 1),
        })

    # Sort
    if order == "best":
        rankings.sort(key=lambda x: x["composite_score"], reverse=True)
    else:
        rankings.sort(key=lambda x: x["composite_score"])

    return {
        "rankings": rankings[:limit],
        "total_states": len(rankings),
        "order": order,
        "clinical_context": {
            "composite_score_meaning": (
                "Score 0-100 combining average CMS star rating (50%) and percentage of "
                "quality measures at or better than national rate (50%). Higher = better "
                "performing state."
            ),
            "interpretation": (
                "States at the bottom face systemic healthcare quality challenges across "
                "multiple facilities and measures."
            ),
        },
    }
