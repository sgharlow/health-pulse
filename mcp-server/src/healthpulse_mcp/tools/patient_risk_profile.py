"""Patient risk profile tool — patient-level risk data from Synthea FHIR data.

When a facility_id is given, returns a summary of high-risk patients at
that facility.  When a patient_id is also provided (or present via
SHARP X-Patient-ID header), returns that individual patient's conditions,
observations, and risk factors.
"""

import logging
from typing import Any, Optional

from healthpulse_mcp.cache import TOOL_TTL, tool_cache
from healthpulse_mcp.fhir_client import fhir_store
from healthpulse_mcp.sharp import get_sharp_context
from healthpulse_mcp.validation import validate_facility_id

logger = logging.getLogger(__name__)

# CMS condition group display names
CMS_GROUP_LABELS = {
    "heart-failure": "Heart Failure (HF)",
    "pneumonia": "Pneumonia (PN)",
    "copd": "COPD",
    "stroke": "Stroke (STK)",
    "ami": "Acute Myocardial Infarction (AMI)",
    "diabetes": "Diabetes Mellitus",
    "hypertension": "Hypertension",
    "ihd": "Ischemic Heart Disease",
    "other": "Other",
}


def _format_observation(obs: dict) -> dict:
    """Extract key fields from a FHIR Observation into a flat dict."""
    code = obs.get("code", {})
    coding = code.get("coding", [{}])[0]
    vq = obs.get("valueQuantity", {})
    return {
        "code": coding.get("code", ""),
        "display": coding.get("display", code.get("text", "")),
        "value": vq.get("value"),
        "unit": vq.get("unit", ""),
        "date": obs.get("effectiveDateTime", ""),
    }


def _format_condition(cond: dict) -> dict:
    """Extract key fields from a FHIR Condition into a flat dict."""
    code = cond.get("code", {})
    coding = code.get("coding", [{}])[0]
    return {
        "code": coding.get("code", ""),
        "display": coding.get("display", code.get("text", "")),
        "cms_group": cond.get("_cms_group", ""),
        "onset": cond.get("onsetDateTime", ""),
        "status": (cond.get("clinicalStatus", {})
                   .get("coding", [{}])[0]
                   .get("code", "unknown")),
    }


def _build_patient_profile(patient_id: str) -> Optional[dict]:
    """Build a complete risk profile for a single patient."""
    summary = fhir_store.get_patient_summary(patient_id)
    if not summary:
        return None

    patient = fhir_store.get_patient(patient_id)
    conditions = fhir_store.get_conditions(patient_id)
    observations = fhir_store.get_observations(patient_id)
    encounters = fhir_store.get_encounters(patient_id)

    # Identify risk factors from observations
    risk_factors = []
    for obs in observations:
        formatted = _format_observation(obs)
        val = formatted.get("value")
        if val is None:
            continue
        # Flag abnormal vitals / labs
        if formatted["code"] == "8480-6" and val > 140:
            risk_factors.append(f"Elevated systolic BP: {val} mmHg")
        elif formatted["code"] == "4548-4" and val > 6.5:
            risk_factors.append(f"Elevated HbA1c: {val}%")
        elif formatted["code"] == "33762-6" and val > 300:
            risk_factors.append(f"Elevated NT-proBNP: {val} pg/mL (heart failure marker)")
        elif formatted["code"] == "2160-0" and val > 1.5:
            risk_factors.append(f"Elevated creatinine: {val} mg/dL (renal concern)")
        elif formatted["code"] == "2339-0" and val > 200:
            risk_factors.append(f"Elevated glucose: {val} mg/dL")
        elif formatted["code"] == "2093-3" and val > 240:
            risk_factors.append(f"High total cholesterol: {val} mg/dL")

    # Compute readmission risk indicator based on conditions + age
    condition_count = len(summary.get("conditions", []))
    age = summary.get("age", 0)
    readmission_risk = "low"
    if condition_count >= 3 and age >= 65:
        readmission_risk = "high"
    elif condition_count >= 2 or age >= 75:
        readmission_risk = "medium"

    name_parts = patient.get("name", [{}])[0] if patient else {}
    given = name_parts.get("given", [""])[0] if name_parts else ""
    family = name_parts.get("family", "") if name_parts else ""

    return {
        "patient_id": patient_id,
        "facility_id": summary.get("facility_id", ""),
        "name": f"{given} {family}".strip(),
        "age": age,
        "gender": summary.get("gender", ""),
        "risk_level": summary.get("risk_level", "unknown"),
        "readmission_risk": readmission_risk,
        "conditions": [_format_condition(c) for c in conditions],
        "cms_groups": [
            CMS_GROUP_LABELS.get(g, g) for g in summary.get("cms_groups", [])
        ],
        "observations": [_format_observation(o) for o in observations],
        "risk_factors": risk_factors,
        "encounter_count": len(encounters),
        "comorbidity_count": condition_count,
    }


async def run(args: dict[str, Any]) -> dict[str, Any]:
    """Execute the patient_risk_profile tool.

    Args:
        args: Tool arguments with keys:
            facility_id (str): CMS facility CCN ID (required)
            patient_id (str, optional): Specific patient UUID to look up

    Returns:
        dict with either a single patient profile or a facility-level
        risk summary.
    """
    # --- Cache check ---
    cache_key = tool_cache.make_key("patient_risk_profile", args)
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    facility_id = validate_facility_id(args.get("facility_id", ""))
    if not facility_id:
        return {"error": "Valid facility_id is required (6-character CMS CCN, e.g. '050454')"}

    # Check SHARP context for patient_id
    patient_id = args.get("patient_id")
    if not patient_id:
        sharp = get_sharp_context()
        if sharp.patient_id:
            patient_id = sharp.patient_id
            logger.info("Using patient_id from SHARP context: %s", patient_id)
        if sharp.fhir_server_url:
            logger.info("SHARP FHIR server URL noted: %s (using local data for demo)",
                        sharp.fhir_server_url)

    # Single patient profile
    if patient_id:
        profile = _build_patient_profile(patient_id)
        if not profile:
            return {
                "error": f"Patient not found: {patient_id}",
                "facility_id": facility_id,
            }
        # Verify patient belongs to the requested facility
        if profile["facility_id"] != facility_id:
            return {
                "error": (
                    f"Patient {patient_id} is not assigned to facility {facility_id} "
                    f"(assigned to {profile['facility_id']})"
                ),
            }
        result = {
            "mode": "single_patient",
            "patient": profile,
            "data_source": "synthea_synthetic",
            "phi_notice": "This is synthetic data generated by Synthea — no real PHI.",
        }
        tool_cache.set(cache_key, result, TOOL_TTL)
        return result

    # Facility-level risk summary
    patients = fhir_store.search_patients(facility_id)
    if not patients:
        return {
            "error": f"No patients found for facility {facility_id}",
            "available_facilities": fhir_store.get_facility_ids(),
        }

    # Group by risk level
    risk_groups: dict[str, list[dict]] = {"high": [], "medium": [], "low": []}
    for p in patients:
        rl = p.get("risk_level", "low")
        risk_groups.setdefault(rl, []).append({
            "patient_id": p["patient_id"],
            "name": p["name"],
            "age": p["age"],
            "conditions": p["conditions"],
            "risk_level": rl,
        })

    result = {
        "mode": "facility_summary",
        "facility_id": facility_id,
        "total_patients": len(patients),
        "risk_distribution": {k: len(v) for k, v in risk_groups.items()},
        "high_risk_patients": risk_groups.get("high", [])[:10],
        "medium_risk_patients": risk_groups.get("medium", [])[:5],
        "clinical_context": {
            "risk_methodology": (
                "Risk level is computed from age (65+ adds 1, 75+ adds 2) and "
                "active condition count. Score >= 3 = high, >= 2 = medium, else low."
            ),
            "use_patient_id": (
                "Pass a specific patient_id to get detailed conditions, "
                "observations, and individual risk factors."
            ),
        },
        "data_source": "synthea_synthetic",
        "phi_notice": "This is synthetic data generated by Synthea — no real PHI.",
    }
    tool_cache.set(cache_key, result, TOOL_TTL)
    return result
