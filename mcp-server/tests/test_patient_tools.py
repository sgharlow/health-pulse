"""Tests for patient_risk_profile and patient_cohort_analysis tools."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from healthpulse_mcp.fhir_client import FHIRDataStore, fhir_store as _module_store
from healthpulse_mcp.sharp import SharpContext, set_sharp_context
from healthpulse_mcp.tools.patient_risk_profile import run as risk_profile_run
from healthpulse_mcp.tools.patient_cohort_analysis import run as cohort_analysis_run


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthea_dir(tmp_path):
    """Create temp dir with test FHIR data matching the fhir_client test fixture."""
    patient_id = "p-risk-001"
    patient_id_2 = "p-risk-002"
    patient_id_3 = "p-risk-003"
    facility_id = "050454"

    bundle = {
        "resourceType": "Bundle",
        "id": "test-bundle",
        "type": "collection",
        "total": 8,
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "identifier": [{"system": "urn:healthpulse:facility", "value": facility_id}],
                    "name": [{"use": "official", "family": "Taylor", "given": ["Alice"]}],
                    "gender": "female",
                    "birthDate": "1950-06-12",
                },
                "fullUrl": f"urn:uuid:{patient_id}",
            },
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id_2,
                    "identifier": [{"system": "urn:healthpulse:facility", "value": facility_id}],
                    "name": [{"use": "official", "family": "Brown", "given": ["Bob"]}],
                    "gender": "male",
                    "birthDate": "1985-11-30",
                },
                "fullUrl": f"urn:uuid:{patient_id_2}",
            },
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id_3,
                    "identifier": [{"system": "urn:healthpulse:facility", "value": "100007"}],
                    "name": [{"use": "official", "family": "Wilson", "given": ["Carol"]}],
                    "gender": "female",
                    "birthDate": "1960-01-01",
                },
                "fullUrl": f"urn:uuid:{patient_id_3}",
            },
            # Encounter for patient 1
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-risk-001",
                    "status": "finished",
                    "class": {"code": "IMP"},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "period": {"start": "2026-01-01", "end": "2026-01-05"},
                },
                "fullUrl": "urn:uuid:enc-risk-001",
            },
            # Conditions for patient 1 (high-risk: HF + hypertension + diabetes)
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-risk-001",
                    "code": {
                        "coding": [{"system": "http://snomed.info/sct", "code": "84114007",
                                     "display": "Heart failure"}],
                    },
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": "Encounter/enc-risk-001"},
                    "onsetDateTime": "2025-06-01",
                    "_cms_group": "heart-failure",
                },
                "fullUrl": "urn:uuid:cond-risk-001",
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-risk-002",
                    "code": {
                        "coding": [{"system": "http://snomed.info/sct", "code": "38341003",
                                     "display": "Hypertensive disorder"}],
                    },
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": "Encounter/enc-risk-001"},
                    "onsetDateTime": "2024-01-01",
                    "_cms_group": "hypertension",
                },
                "fullUrl": "urn:uuid:cond-risk-002",
            },
            # Observation: high BP for patient 1
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-risk-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "8480-6",
                                     "display": "Systolic blood pressure"}],
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": "Encounter/enc-risk-001"},
                    "effectiveDateTime": "2026-01-02",
                    "valueQuantity": {"value": 165, "unit": "mmHg"},
                },
                "fullUrl": "urn:uuid:obs-risk-001",
            },
            # Observation: elevated HbA1c for patient 1
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-risk-002",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "4548-4",
                                     "display": "Hemoglobin A1c"}],
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": "Encounter/enc-risk-001"},
                    "effectiveDateTime": "2026-01-02",
                    "valueQuantity": {"value": 8.1, "unit": "%"},
                },
                "fullUrl": "urn:uuid:obs-risk-002",
            },
        ],
    }

    # Write bundle
    with open(tmp_path / "fhir_bundle.json", "w") as f:
        json.dump(bundle, f)

    # Write patient index
    index = {
        "generated": "2026-03-15",
        "total_patients": 3,
        "facility_ids": [facility_id, "100007"],
        "patients": [
            {
                "patient_id": patient_id,
                "facility_id": facility_id,
                "name": "Alice Taylor",
                "age": 75,
                "gender": "female",
                "conditions": ["Heart failure", "Hypertensive disorder"],
                "cms_groups": ["heart-failure", "hypertension"],
                "num_encounters": 1,
                "num_observations": 2,
                "risk_level": "high",
            },
            {
                "patient_id": patient_id_2,
                "facility_id": facility_id,
                "name": "Bob Brown",
                "age": 40,
                "gender": "male",
                "conditions": ["Pneumonia"],
                "cms_groups": ["pneumonia"],
                "num_encounters": 1,
                "num_observations": 1,
                "risk_level": "low",
            },
            {
                "patient_id": patient_id_3,
                "facility_id": "100007",
                "name": "Carol Wilson",
                "age": 66,
                "gender": "female",
                "conditions": ["COPD", "Diabetes"],
                "cms_groups": ["copd", "diabetes"],
                "num_encounters": 1,
                "num_observations": 1,
                "risk_level": "medium",
            },
        ],
    }
    with open(tmp_path / "patient_index.json", "w") as f:
        json.dump(index, f)

    return tmp_path


@pytest.fixture(autouse=True)
def _patch_fhir_store(synthea_dir):
    """Replace the module-level fhir_store singleton with test data."""
    test_store = FHIRDataStore(data_dir=synthea_dir)
    test_store.load()
    with patch("healthpulse_mcp.tools.patient_risk_profile.fhir_store", test_store), \
         patch("healthpulse_mcp.tools.patient_cohort_analysis.fhir_store", test_store):
        yield test_store


@pytest.fixture(autouse=True)
def _reset_sharp_context():
    """Reset SHARP context before each test."""
    set_sharp_context(SharpContext())
    yield
    set_sharp_context(SharpContext())


# ===========================================================================
# patient_risk_profile tests
# ===========================================================================

class TestPatientRiskProfileValidation:
    @pytest.mark.asyncio
    async def test_missing_facility_id(self):
        result = await risk_profile_run({"facility_id": ""})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_facility_id(self):
        result = await risk_profile_run({"facility_id": "INVALID!"})
        assert "error" in result


class TestPatientRiskProfileSinglePatient:
    @pytest.mark.asyncio
    async def test_single_patient_mode(self):
        result = await risk_profile_run({
            "facility_id": "050454",
            "patient_id": "p-risk-001",
        })
        assert result["mode"] == "single_patient"
        assert result["patient"]["patient_id"] == "p-risk-001"
        assert result["patient"]["name"] == "Alice Taylor"
        assert result["data_source"] == "synthea_synthetic"

    @pytest.mark.asyncio
    async def test_single_patient_conditions(self):
        result = await risk_profile_run({
            "facility_id": "050454",
            "patient_id": "p-risk-001",
        })
        conditions = result["patient"]["conditions"]
        displays = {c["display"] for c in conditions}
        assert "Heart failure" in displays

    @pytest.mark.asyncio
    async def test_single_patient_observations(self):
        result = await risk_profile_run({
            "facility_id": "050454",
            "patient_id": "p-risk-001",
        })
        obs = result["patient"]["observations"]
        assert len(obs) == 2
        codes = {o["code"] for o in obs}
        assert "8480-6" in codes

    @pytest.mark.asyncio
    async def test_single_patient_risk_factors(self):
        result = await risk_profile_run({
            "facility_id": "050454",
            "patient_id": "p-risk-001",
        })
        risk_factors = result["patient"]["risk_factors"]
        # Patient has BP 165 and HbA1c 8.1 — both should trigger risk factors
        assert any("BP" in f or "systolic" in f.lower() for f in risk_factors)
        assert any("HbA1c" in f for f in risk_factors)

    @pytest.mark.asyncio
    async def test_patient_not_found(self):
        result = await risk_profile_run({
            "facility_id": "050454",
            "patient_id": "nonexistent-uuid",
        })
        assert "error" in result

    @pytest.mark.asyncio
    async def test_patient_wrong_facility(self):
        """Patient exists but belongs to a different facility."""
        result = await risk_profile_run({
            "facility_id": "050454",
            "patient_id": "p-risk-003",  # belongs to 100007
        })
        assert "error" in result


class TestPatientRiskProfileFacilitySummary:
    @pytest.mark.asyncio
    async def test_facility_summary_mode(self):
        result = await risk_profile_run({"facility_id": "050454"})
        assert result["mode"] == "facility_summary"
        assert result["facility_id"] == "050454"
        assert result["total_patients"] == 2

    @pytest.mark.asyncio
    async def test_facility_risk_distribution(self):
        result = await risk_profile_run({"facility_id": "050454"})
        dist = result["risk_distribution"]
        assert dist["high"] == 1  # Alice
        assert dist["low"] == 1  # Bob

    @pytest.mark.asyncio
    async def test_facility_not_found(self):
        result = await risk_profile_run({"facility_id": "999999"})
        assert "error" in result
        assert "available_facilities" in result


class TestPatientRiskProfileSHARP:
    @pytest.mark.asyncio
    async def test_sharp_patient_id_used(self):
        """When SHARP X-Patient-ID is set, it's used as default patient_id."""
        set_sharp_context(SharpContext(patient_id="p-risk-001"))
        result = await risk_profile_run({"facility_id": "050454"})
        assert result["mode"] == "single_patient"
        assert result["patient"]["patient_id"] == "p-risk-001"

    @pytest.mark.asyncio
    async def test_explicit_patient_id_overrides_sharp(self):
        """Explicit patient_id should be used over SHARP context."""
        set_sharp_context(SharpContext(patient_id="p-risk-001"))
        result = await risk_profile_run({
            "facility_id": "050454",
            "patient_id": "p-risk-002",
        })
        # Bob is low risk, no conditions in bundle
        assert result["mode"] == "single_patient"
        assert result["patient"]["patient_id"] == "p-risk-002"


# ===========================================================================
# patient_cohort_analysis tests
# ===========================================================================

class TestCohortAnalysisValidation:
    @pytest.mark.asyncio
    async def test_missing_facility_id(self):
        result = await cohort_analysis_run({"facility_id": ""})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_condition(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "condition": "invalid-condition",
        })
        assert "error" in result
        assert "valid_conditions" in result

    @pytest.mark.asyncio
    async def test_invalid_risk_level(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "risk_level": "extreme",
        })
        assert "error" in result
        assert "valid_risk_levels" in result


class TestCohortAnalysisResults:
    @pytest.mark.asyncio
    async def test_basic_cohort(self):
        result = await cohort_analysis_run({"facility_id": "050454"})
        assert "cohort" in result
        assert result["cohort"]["patient_count"] == 2
        assert result["facility_id"] == "050454"
        assert result["data_source"] == "synthea_synthetic"

    @pytest.mark.asyncio
    async def test_cohort_with_condition_filter(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "condition": "heart-failure",
        })
        assert result["cohort"]["patient_count"] == 1
        assert result["filters"]["condition"] == "heart-failure"

    @pytest.mark.asyncio
    async def test_cohort_with_risk_level_filter(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "risk_level": "high",
        })
        assert result["cohort"]["patient_count"] == 1
        assert result["filters"]["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_cohort_readmission_indicators(self):
        result = await cohort_analysis_run({"facility_id": "050454"})
        ri = result["readmission_indicators"]
        assert "cohort_readmission_risk_score" in ri
        assert "interpretation" in ri

    @pytest.mark.asyncio
    async def test_cohort_clinical_context(self):
        result = await cohort_analysis_run({"facility_id": "050454"})
        ctx = result["clinical_context"]
        assert "comorbidity_insight" in ctx
        assert "age_insight" in ctx

    @pytest.mark.asyncio
    async def test_cohort_cms_context_with_condition(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "condition": "heart-failure",
        })
        cms = result["cms_context"]
        assert "related_cms_measures" in cms
        assert "MORT_30_HF" in cms["related_cms_measures"]

    @pytest.mark.asyncio
    async def test_cohort_cms_context_without_condition(self):
        result = await cohort_analysis_run({"facility_id": "050454"})
        # No condition filter = no CMS context
        assert result["cms_context"] == {}


class TestCohortAnalysisEdgeCases:
    @pytest.mark.asyncio
    async def test_no_patients_for_facility(self):
        result = await cohort_analysis_run({"facility_id": "999999"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_no_patients_for_condition(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "condition": "stroke",
        })
        assert "error" in result

    @pytest.mark.asyncio
    async def test_combined_condition_and_risk(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "condition": "heart-failure",
            "risk_level": "high",
        })
        assert result["cohort"]["patient_count"] == 1

    @pytest.mark.asyncio
    async def test_combined_filters_no_match(self):
        result = await cohort_analysis_run({
            "facility_id": "050454",
            "condition": "pneumonia",
            "risk_level": "high",
        })
        assert result["patient_count"] == 0
