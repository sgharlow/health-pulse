"""Patient experience tool -- analyzes HCAHPS patient satisfaction scores."""

import os
from typing import Any

from healthpulse_mcp.cache import TOOL_TTL, tool_cache
from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_state

# Maps measure category to HCAHPS measure ID patterns
MEASURE_CATEGORY_PATTERNS: dict[str, list[str]] = {
    "communication": ["COMM", "H_COMP_1", "H_COMP_2", "H_COMP_3"],
    "responsiveness": ["H_COMP_5", "H_RESP"],
    "environment": ["H_CLEAN", "H_QUIET", "H_COMP_6"],
    "overall": ["H_HSP_RATING", "H_RECMND", "H_STAR_RATING"],
}

VALID_CATEGORIES = list(MEASURE_CATEGORY_PATTERNS.keys()) + ["all"]


def _classify_measure(measure_id: str) -> str | None:
    """Return the category name for an HCAHPS measure ID, or None if unmatched."""
    upper = measure_id.upper()
    for category, patterns in MEASURE_CATEGORY_PATTERNS.items():
        if any(pat in upper for pat in patterns):
            return category
    return None


def _safe_float(value: Any) -> float | None:
    """Convert a value to float, returning None if not parseable.

    Handles special values like "Not Applicable" and "Not Available" that
    appear in CMS HCAHPS data.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower().startswith("not "):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _get_score(row: dict[str, Any]) -> float | None:
    """Extract the best available numeric score from an HCAHPS row.

    Tries patient_survey_star_rating first. If that is non-numeric
    (e.g. "Not Applicable"), falls back to hcahps_answer_percent.
    """
    star = _safe_float(row.get("patient_survey_star_rating"))
    if star is not None:
        return star
    return _safe_float(row.get("hcahps_answer_percent"))


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Analyze HCAHPS patient experience scores across facilities.

    Args:
        domo: Authenticated DomoClient
        args: Tool arguments with keys:
            state (str, optional): Two-letter state code filter
            measure (str): One of communication|responsiveness|environment|overall|all
            min_star_rating (float, optional): Filter to facilities below this star rating
            limit (int): Max worst facilities to return (default 20)

    Returns:
        dict with total_facilities_analyzed, measure_category, summary,
        worst_facilities, category_averages, clinical_context, filters
    """
    # --- Cache check ---
    cache_key = tool_cache.make_key("patient_experience", args)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    dataset_id = os.environ.get("HP_EXPERIENCE_DATASET_ID")
    if not dataset_id:
        return {"error": "HP_EXPERIENCE_DATASET_ID environment variable not set"}

    state = validate_state(args.get("state"))
    measure = args.get("measure", "all")
    min_star_rating = _safe_float(args.get("min_star_rating"))
    limit = int(args.get("limit", 20))

    if measure not in VALID_CATEGORIES:
        return {"error": f"Invalid measure category: {measure!r}. Must be one of {VALID_CATEGORIES}"}

    # If a state filter is requested, query facilities first to get facility_ids
    # in that state (HCAHPS dataset may not have state column).
    state_facility_ids: set[str] | None = None
    facility_lookup: dict[str, dict[str, Any]] = {}
    if state:
        facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID")
        if not facilities_id:
            return {"error": "HP_FACILITIES_DATASET_ID environment variable not set (required for state filter)"}
        try:
            fac_sql = f"SELECT facility_id, facility_name, state FROM table WHERE state = '{state}'"
            fac_rows = domo.query_as_dicts(facilities_id, fac_sql)
            state_facility_ids = {str(r.get("facility_id")) for r in fac_rows}
            facility_lookup = {str(r.get("facility_id")): r for r in fac_rows}
        except Exception as exc:
            return {"error": f"Facilities query failed: {exc}"}

    # Query HCAHPS dataset
    sql = "SELECT facility_id, hcahps_measure_id, patient_survey_star_rating, hcahps_answer_percent, hcahps_question, number_of_completed_surveys FROM table"

    try:
        rows = domo.query_as_dicts(dataset_id, sql)
    except Exception as exc:
        return {"error": f"Query failed: {exc}"}

    # Apply state filter in Python
    if state_facility_ids is not None:
        rows = [r for r in rows if str(r.get("facility_id")) in state_facility_ids]

    # Classify each row into a measure category
    classified_rows: list[tuple[str, dict[str, Any]]] = []
    for row in rows:
        mid = str(row.get("hcahps_measure_id", ""))
        cat = _classify_measure(mid)
        if cat is not None:
            classified_rows.append((cat, row))

    # Filter by requested measure category
    if measure != "all":
        classified_rows = [(cat, row) for cat, row in classified_rows if cat == measure]

    # Apply min_star_rating filter (keep facilities BELOW this threshold)
    if min_star_rating is not None:
        filtered = []
        for cat, row in classified_rows:
            sr = _get_score(row)
            if sr is not None and sr < min_star_rating:
                filtered.append((cat, row))
        classified_rows = filtered

    # Compute category averages
    category_scores: dict[str, list[float]] = {}
    for cat, row in classified_rows:
        sr = _get_score(row)
        if sr is not None:
            category_scores.setdefault(cat, []).append(sr)

    category_averages: dict[str, float] = {}
    for cat, scores in category_scores.items():
        if scores:
            category_averages[cat] = round(sum(scores) / len(scores), 2)

    # Compute per-facility average experience rating
    facility_scores: dict[str, list[float]] = {}
    facility_measures: dict[str, dict[str, float]] = {}
    for cat, row in classified_rows:
        fid = str(row.get("facility_id", ""))
        sr = _get_score(row)
        if sr is not None and fid:
            facility_scores.setdefault(fid, []).append(sr)
            # Track per-category score for this facility
            fac_cats = facility_measures.setdefault(fid, {})
            fac_cats.setdefault(cat, [])
            # Store raw; we'll average later
            if isinstance(fac_cats[cat], list):
                fac_cats[cat].append(sr)

    # Average the per-category scores per facility
    for fid in facility_measures:
        for cat in facility_measures[fid]:
            scores_list = facility_measures[fid][cat]
            if isinstance(scores_list, list) and scores_list:
                facility_measures[fid][cat] = round(sum(scores_list) / len(scores_list), 2)

    # Build worst facilities list (lowest average experience rating)
    facility_avg: list[dict[str, Any]] = []
    for fid, scores in facility_scores.items():
        avg = round(sum(scores) / len(scores), 2)
        # Find lowest measure category for this facility
        fac_cats = facility_measures.get(fid, {})
        lowest_cat = None
        lowest_val = float("inf")
        for cat, val in fac_cats.items():
            if isinstance(val, (int, float)) and val < lowest_val:
                lowest_val = val
                lowest_cat = cat

        entry: dict[str, Any] = {
            "facility_id": fid,
            "avg_experience_rating": avg,
            "lowest_measure": lowest_cat,
        }
        # Add facility name and state from lookup if available
        if fid in facility_lookup:
            entry["facility_name"] = facility_lookup[fid].get("facility_name", "")
            entry["state"] = facility_lookup[fid].get("state", "")
        facility_avg.append(entry)

    facility_avg.sort(key=lambda x: x["avg_experience_rating"])
    worst_facilities = facility_avg[:limit]

    # Compute overall summary
    all_star_ratings = []
    for scores in facility_scores.values():
        all_star_ratings.extend(scores)

    avg_star = round(sum(all_star_ratings) / len(all_star_ratings), 2) if all_star_ratings else 0.0
    lowest_category = min(category_averages, key=category_averages.get) if category_averages else None  # type: ignore[arg-type]
    lowest_category_avg = category_averages.get(lowest_category, 0.0) if lowest_category else 0.0

    facility_ids = {str(r.get("facility_id")) for _, r in classified_rows}

    result: dict[str, Any] = {
        "total_facilities_analyzed": len(facility_ids),
        "measure_category": measure,
        "summary": {
            "avg_star_rating": avg_star,
            "lowest_category": lowest_category,
            "lowest_category_avg": round(lowest_category_avg, 2),
        },
        "worst_facilities": worst_facilities,
        "category_averages": category_averages,
        "clinical_context": {
            "about_hcahps": (
                "Hospital Consumer Assessment of Healthcare Providers and Systems (HCAHPS) "
                "is a CMS-mandated standardized patient experience survey administered to a "
                "random sample of adult inpatients between 48 hours and 6 weeks after discharge. "
                "Results are publicly reported to encourage hospitals to improve quality of care."
            ),
            "why_it_matters": (
                "HCAHPS scores directly affect CMS Value-Based Purchasing (VBP) payments — "
                "hospitals with low patient experience scores receive reduced Medicare "
                "reimbursements. Patient experience is also correlated with clinical outcomes, "
                "including lower readmission rates and better medication adherence."
            ),
            "measure_categories": {
                "communication": "Nurse communication, doctor communication, and staff communication with patients",
                "responsiveness": "How quickly staff respond to patient call buttons and requests for help",
                "environment": "Hospital cleanliness and quietness at night",
                "overall": "Overall hospital rating (0-10 scale) and willingness to recommend",
            },
        },
        "filters": {
            "state": state,
            "measure": measure,
            "min_star_rating": min_star_rating,
            "limit": limit,
        },
    }

    tool_cache.set(cache_key, result, TOOL_TTL)
    return result
