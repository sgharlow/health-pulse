"""Patient cohort analysis tool — cohort statistics from Synthea FHIR data.

Given a facility_id and optional condition / risk filters, returns
cohort demographics, comorbidity patterns, and readmission risk
indicators.  Connects synthetic patient data to aggregate CMS measures
for a richer analytical picture.
"""

import logging
from typing import Any, Optional

from healthpulse_mcp.cache import TOOL_TTL, tool_cache
from healthpulse_mcp.fhir_client import fhir_store
from healthpulse_mcp.sharp import get_sharp_context
from healthpulse_mcp.validation import validate_facility_id

logger = logging.getLogger(__name__)

# Valid CMS condition groups that map to quality measures
VALID_CONDITIONS = {
    "heart-failure", "pneumonia", "copd", "stroke", "ami",
    "diabetes", "hypertension", "ihd",
}

# CMS measure IDs associated with each condition group
CMS_MEASURE_MAP = {
    "heart-failure": ["MORT_30_HF", "READM_30_HF"],
    "pneumonia": ["MORT_30_PN", "READM_30_PN"],
    "copd": ["MORT_30_COPD", "READM_30_COPD"],
    "stroke": ["MORT_30_STK"],
    "ami": ["MORT_30_AMI", "READM_30_AMI"],
}

VALID_RISK_LEVELS = {"high", "medium", "low"}


async def run(args: dict[str, Any]) -> dict[str, Any]:
    """Execute the patient_cohort_analysis tool.

    Args:
        args: Tool arguments with keys:
            facility_id (str): CMS facility CCN ID (required)
            condition (str, optional): CMS condition group filter
            risk_level (str, optional): Filter by risk level (high/medium/low)

    Returns:
        dict with cohort statistics, comorbidity patterns, and CMS
        measure context.
    """
    # --- Cache check ---
    cache_key = tool_cache.make_key("patient_cohort_analysis", args)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    facility_id = validate_facility_id(args.get("facility_id", ""))
    if not facility_id:
        return {"error": "Valid facility_id is required (6-character CMS CCN, e.g. '050454')"}

    condition = args.get("condition")
    risk_level = args.get("risk_level")

    # Validate condition if provided
    if condition and condition not in VALID_CONDITIONS:
        return {
            "error": f"Unknown condition: {condition!r}",
            "valid_conditions": sorted(VALID_CONDITIONS),
        }

    # Validate risk_level if provided
    if risk_level and risk_level not in VALID_RISK_LEVELS:
        return {
            "error": f"Unknown risk_level: {risk_level!r}",
            "valid_risk_levels": sorted(VALID_RISK_LEVELS),
        }

    # Log SHARP context if present
    sharp = get_sharp_context()
    if sharp.fhir_server_url:
        logger.info("SHARP FHIR server URL noted: %s (using local data for demo)",
                    sharp.fhir_server_url)
    if sharp.patient_id:
        logger.info("SHARP patient_id context available: %s", sharp.patient_id)

    # Get cohort statistics from FHIR data store
    stats = fhir_store.get_cohort_stats(facility_id, cms_group=condition)
    if stats.get("patient_count", 0) == 0:
        return {
            "error": f"No patients found for facility {facility_id}"
                     + (f" with condition {condition}" if condition else ""),
            "facility_id": facility_id,
            "condition": condition,
            "available_facilities": fhir_store.get_facility_ids(),
        }

    # Apply risk_level filter if specified
    if risk_level:
        filtered_patients = fhir_store.get_patients_by_risk(facility_id, risk_level)
        if condition:
            filtered_patients = [
                p for p in filtered_patients
                if condition in p.get("cms_groups", [])
            ]

        if not filtered_patients:
            return {
                "facility_id": facility_id,
                "condition": condition,
                "risk_level": risk_level,
                "patient_count": 0,
                "message": f"No {risk_level}-risk patients found"
                           + (f" with {condition}" if condition else "")
                           + f" at facility {facility_id}",
            }

        # Recompute stats for filtered cohort
        ages = [p["age"] for p in filtered_patients]
        genders = [p["gender"] for p in filtered_patients]
        all_conditions: dict[str, int] = {}
        all_groups: dict[str, int] = {}
        for p in filtered_patients:
            for c in p.get("conditions", []):
                all_conditions[c] = all_conditions.get(c, 0) + 1
            for g in p.get("cms_groups", []):
                all_groups[g] = all_groups.get(g, 0) + 1

        multi_comorbid = sum(1 for p in filtered_patients if len(p.get("conditions", [])) >= 3)

        stats = {
            "patient_count": len(filtered_patients),
            "facility_id": facility_id,
            "condition_filter": condition,
            "avg_age": round(sum(ages) / len(ages), 1),
            "age_range": {"min": min(ages), "max": max(ages)},
            "gender_split": {
                "male": sum(1 for g in genders if g == "male"),
                "female": sum(1 for g in genders if g == "female"),
            },
            "risk_distribution": {risk_level: len(filtered_patients)},
            "patients_with_2plus_comorbidities": multi_comorbid,
            "comorbidity_rate": round(multi_comorbid / len(filtered_patients), 2),
            "common_conditions": dict(
                sorted(all_conditions.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "cms_group_distribution": dict(
                sorted(all_groups.items(), key=lambda x: x[1], reverse=True)
            ),
        }

    # Build readmission risk indicators
    readmission_indicators = _compute_readmission_indicators(stats, condition)

    # Build CMS measure context
    cms_context = {}
    if condition and condition in CMS_MEASURE_MAP:
        cms_context = {
            "related_cms_measures": CMS_MEASURE_MAP[condition],
            "clinical_relevance": (
                f"CMS tracks {condition.replace('-', ' ')} outcomes via "
                f"{', '.join(CMS_MEASURE_MAP[condition])}. "
                f"This cohort of {stats['patient_count']} patients at facility "
                f"{facility_id} provides the patient-level detail behind those "
                f"aggregate measures."
            ),
        }

    result: dict[str, Any] = {
        "facility_id": facility_id,
        "cohort": stats,
        "filters": {
            "condition": condition,
            "risk_level": risk_level,
        },
        "readmission_indicators": readmission_indicators,
        "cms_context": cms_context,
        "clinical_context": {
            "comorbidity_insight": _comorbidity_insight(stats),
            "age_insight": _age_insight(stats),
        },
        "data_source": "synthea_synthetic",
        "phi_notice": "This is synthetic data generated by Synthea — no real PHI.",
    }

    tool_cache.set(cache_key, result, TOOL_TTL)
    return result


def _compute_readmission_indicators(stats: dict, condition: Optional[str]) -> dict:
    """Compute readmission risk indicators from cohort statistics."""
    patient_count = stats.get("patient_count", 0)
    if patient_count == 0:
        return {}

    high_risk_count = stats.get("risk_distribution", {}).get("high", 0)
    comorbidity_rate = stats.get("comorbidity_rate", 0)
    avg_age = stats.get("avg_age", 0)

    # Risk score: weighted combination of factors
    risk_score = (
        (high_risk_count / patient_count) * 40 +
        comorbidity_rate * 30 +
        (min(avg_age, 90) / 90) * 30
    )
    risk_score = round(min(risk_score, 100), 1)

    return {
        "cohort_readmission_risk_score": risk_score,
        "high_risk_patient_pct": round(high_risk_count / patient_count * 100, 1),
        "comorbidity_burden_pct": round(comorbidity_rate * 100, 1),
        "avg_age": avg_age,
        "interpretation": (
            f"{'High' if risk_score >= 60 else 'Moderate' if risk_score >= 40 else 'Low'} "
            f"readmission risk cohort (score {risk_score}/100). "
            f"{high_risk_count} of {patient_count} patients are high-risk, "
            f"and {round(comorbidity_rate * 100)}% have 2+ comorbidities."
        ),
    }


def _comorbidity_insight(stats: dict) -> str:
    """Generate a natural-language comorbidity insight."""
    rate = stats.get("comorbidity_rate", 0)
    count = stats.get("patients_with_2plus_comorbidities", 0)
    total = stats.get("patient_count", 0)
    if total == 0:
        return "No patients in cohort."
    if rate >= 0.5:
        return (
            f"High comorbidity burden: {count} of {total} patients ({round(rate*100)}%) "
            f"have 2+ active conditions. This population likely drives disproportionate "
            f"readmission and mortality rates."
        )
    if rate >= 0.25:
        return (
            f"Moderate comorbidity burden: {count} of {total} patients ({round(rate*100)}%) "
            f"have 2+ active conditions."
        )
    return (
        f"Low comorbidity burden: only {count} of {total} patients ({round(rate*100)}%) "
        f"have 2+ active conditions."
    )


def _age_insight(stats: dict) -> str:
    """Generate a natural-language age insight."""
    avg = stats.get("avg_age", 0)
    age_range = stats.get("age_range", {})
    if avg >= 75:
        return (
            f"Elderly cohort (avg age {avg}, range {age_range.get('min', '?')}-"
            f"{age_range.get('max', '?')}). Age alone is a significant risk factor "
            f"for readmission and mortality."
        )
    if avg >= 65:
        return (
            f"Senior cohort (avg age {avg}, range {age_range.get('min', '?')}-"
            f"{age_range.get('max', '?')}). Medicare-eligible population."
        )
    return (
        f"Mixed-age cohort (avg age {avg}, range {age_range.get('min', '?')}-"
        f"{age_range.get('max', '?')})."
    )
