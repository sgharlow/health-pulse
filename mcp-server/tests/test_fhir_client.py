"""Tests for the FHIR data layer (fhir_client.py)."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from healthpulse_mcp.fhir_client import FHIRDataStore


# ---------------------------------------------------------------------------
# Fixtures — minimal FHIR data for fast, isolated tests
# ---------------------------------------------------------------------------

@pytest.fixture
def synthea_dir(tmp_path):
    """Create a temp directory with minimal Synthea-style FHIR data."""
    patient_id = "test-patient-001"
    patient_id_2 = "test-patient-002"
    facility_id = "050454"
    facility_id_2 = "100007"
    condition_id = "cond-001"
    condition_id_2 = "cond-002"
    obs_id = "obs-001"
    obs_id_2 = "obs-002"
    enc_id = "enc-001"

    bundle = {
        "resourceType": "Bundle",
        "id": "test-bundle",
        "type": "collection",
        "total": 7,
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "identifier": [
                        {"system": "urn:healthpulse:facility", "value": facility_id},
                    ],
                    "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                    "gender": "female",
                    "birthDate": "1955-03-15",
                },
                "fullUrl": f"urn:uuid:{patient_id}",
            },
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id_2,
                    "identifier": [
                        {"system": "urn:healthpulse:facility", "value": facility_id_2},
                    ],
                    "name": [{"use": "official", "family": "Smith", "given": ["John"]}],
                    "gender": "male",
                    "birthDate": "1948-07-20",
                },
                "fullUrl": f"urn:uuid:{patient_id_2}",
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": enc_id,
                    "status": "finished",
                    "class": {"code": "IMP"},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "period": {"start": "2026-01-01", "end": "2026-01-05"},
                    "serviceProvider": {
                        "identifier": {"system": "urn:healthpulse:facility", "value": facility_id}
                    },
                },
                "fullUrl": f"urn:uuid:{enc_id}",
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": condition_id,
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                     "code": "active"}],
                    },
                    "code": {
                        "coding": [{"system": "http://snomed.info/sct",
                                     "code": "84114007",
                                     "display": "Heart failure"}],
                        "text": "Heart failure",
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "_cms_group": "heart-failure",
                },
                "fullUrl": f"urn:uuid:{condition_id}",
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": condition_id_2,
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                     "code": "active"}],
                    },
                    "code": {
                        "coding": [{"system": "http://snomed.info/sct",
                                     "code": "38341003",
                                     "display": "Hypertensive disorder"}],
                        "text": "Hypertensive disorder",
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "_cms_group": "hypertension",
                },
                "fullUrl": f"urn:uuid:{condition_id_2}",
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org",
                                     "code": "8480-6",
                                     "display": "Systolic blood pressure"}],
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "effectiveDateTime": "2026-01-02",
                    "valueQuantity": {"value": 155, "unit": "mmHg"},
                },
                "fullUrl": f"urn:uuid:{obs_id}",
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id_2,
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org",
                                     "code": "4548-4",
                                     "display": "Hemoglobin A1c"}],
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "effectiveDateTime": "2026-01-02",
                    "valueQuantity": {"value": 7.2, "unit": "%"},
                },
                "fullUrl": f"urn:uuid:{obs_id_2}",
            },
        ],
    }

    # Write bundle
    bundle_path = tmp_path / "fhir_bundle.json"
    with open(bundle_path, "w") as f:
        json.dump(bundle, f)

    # Write patient index
    index = {
        "generated": "2026-03-15",
        "total_patients": 2,
        "facility_ids": [facility_id, facility_id_2],
        "patients": [
            {
                "patient_id": patient_id,
                "facility_id": facility_id,
                "name": "Jane Doe",
                "age": 71,
                "gender": "female",
                "conditions": ["Heart failure", "Hypertensive disorder"],
                "cms_groups": ["heart-failure", "hypertension"],
                "num_encounters": 1,
                "num_observations": 2,
                "risk_level": "high",
            },
            {
                "patient_id": patient_id_2,
                "facility_id": facility_id_2,
                "name": "John Smith",
                "age": 77,
                "gender": "male",
                "conditions": ["Pneumonia"],
                "cms_groups": ["pneumonia"],
                "num_encounters": 1,
                "num_observations": 1,
                "risk_level": "medium",
            },
        ],
    }
    index_path = tmp_path / "patient_index.json"
    with open(index_path, "w") as f:
        json.dump(index, f)

    return tmp_path


@pytest.fixture
def fhir_store(synthea_dir):
    """Return a FHIRDataStore loaded from test data."""
    store = FHIRDataStore(data_dir=synthea_dir)
    store.load()
    return store


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFHIRDataStoreLoading:
    def test_load_sets_loaded_flag(self, fhir_store):
        assert fhir_store.is_loaded is True

    def test_patient_count(self, fhir_store):
        assert fhir_store.patient_count == 2

    def test_load_empty_dir(self, tmp_path):
        """Loading from empty dir succeeds with zero patients."""
        store = FHIRDataStore(data_dir=tmp_path)
        store.load()
        assert store.is_loaded is True
        assert store.patient_count == 0


class TestPatientQueries:
    def test_get_patient_exists(self, fhir_store):
        patient = fhir_store.get_patient("test-patient-001")
        assert patient is not None
        assert patient["resourceType"] == "Patient"
        assert patient["gender"] == "female"

    def test_get_patient_not_found(self, fhir_store):
        assert fhir_store.get_patient("nonexistent") is None

    def test_get_patient_summary(self, fhir_store):
        summary = fhir_store.get_patient_summary("test-patient-001")
        assert summary is not None
        assert summary["name"] == "Jane Doe"
        assert summary["risk_level"] == "high"
        assert "heart-failure" in summary["cms_groups"]

    def test_search_patients_by_facility(self, fhir_store):
        patients = fhir_store.search_patients("050454")
        assert len(patients) == 1
        assert patients[0]["patient_id"] == "test-patient-001"

    def test_search_patients_empty_facility(self, fhir_store):
        patients = fhir_store.search_patients("999999")
        assert patients == []


class TestConditionQueries:
    def test_get_conditions(self, fhir_store):
        conditions = fhir_store.get_conditions("test-patient-001")
        assert len(conditions) == 2
        displays = {c["code"]["coding"][0]["display"] for c in conditions}
        assert "Heart failure" in displays
        assert "Hypertensive disorder" in displays

    def test_get_conditions_no_conditions(self, fhir_store):
        # Patient 2 has no conditions in the bundle (only in index)
        conditions = fhir_store.get_conditions("test-patient-002")
        assert conditions == []

    def test_get_patients_by_condition(self, fhir_store):
        patients = fhir_store.get_patients_by_condition("050454", "heart-failure")
        assert len(patients) == 1
        assert patients[0]["patient_id"] == "test-patient-001"

    def test_get_patients_by_condition_no_match(self, fhir_store):
        patients = fhir_store.get_patients_by_condition("050454", "stroke")
        assert patients == []


class TestObservationQueries:
    def test_get_observations(self, fhir_store):
        obs = fhir_store.get_observations("test-patient-001")
        assert len(obs) == 2
        codes = {o["code"]["coding"][0]["code"] for o in obs}
        assert "8480-6" in codes  # systolic BP
        assert "4548-4" in codes  # HbA1c

    def test_get_observations_empty(self, fhir_store):
        obs = fhir_store.get_observations("test-patient-002")
        assert obs == []


class TestEncounterQueries:
    def test_get_encounters(self, fhir_store):
        encounters = fhir_store.get_encounters("test-patient-001")
        assert len(encounters) == 1
        assert encounters[0]["status"] == "finished"


class TestFacilityQueries:
    def test_get_facility_id(self, fhir_store):
        assert fhir_store.get_facility_id("test-patient-001") == "050454"
        assert fhir_store.get_facility_id("test-patient-002") == "100007"

    def test_get_facility_id_unknown(self, fhir_store):
        assert fhir_store.get_facility_id("unknown") is None

    def test_get_facility_ids(self, fhir_store):
        ids = fhir_store.get_facility_ids()
        assert "050454" in ids
        assert "100007" in ids

    def test_get_patients_by_risk(self, fhir_store):
        high = fhir_store.get_patients_by_risk("050454", "high")
        assert len(high) == 1
        low = fhir_store.get_patients_by_risk("050454", "low")
        assert len(low) == 0


class TestCohortStats:
    def test_cohort_stats_all_patients(self, fhir_store):
        stats = fhir_store.get_cohort_stats("050454")
        assert stats["patient_count"] == 1
        assert stats["facility_id"] == "050454"
        assert stats["avg_age"] == 71

    def test_cohort_stats_with_condition(self, fhir_store):
        stats = fhir_store.get_cohort_stats("050454", cms_group="heart-failure")
        assert stats["patient_count"] == 1

    def test_cohort_stats_no_match(self, fhir_store):
        stats = fhir_store.get_cohort_stats("050454", cms_group="stroke")
        assert stats["patient_count"] == 0

    def test_cohort_stats_empty_facility(self, fhir_store):
        stats = fhir_store.get_cohort_stats("999999")
        assert stats["patient_count"] == 0


class TestLazyLoading:
    def test_auto_loads_on_query(self, synthea_dir):
        """Store should auto-load when a query is made."""
        store = FHIRDataStore(data_dir=synthea_dir)
        assert store.is_loaded is False
        patient = store.get_patient("test-patient-001")
        assert store.is_loaded is True
        assert patient is not None
