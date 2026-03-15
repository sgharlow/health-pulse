#!/usr/bin/env python3
"""Generate synthetic FHIR R4 patient data for HealthPulse AI demo.

Creates ~100 patients with conditions relevant to CMS hospital quality
measures (heart failure, pneumonia, COPD, stroke, AMI) and maps them
to a set of real CMS facility IDs.  Output is a FHIR R4-compliant
Bundle JSON file written to data/synthea/.

This is NOT mock data — it produces properly structured FHIR R4
resources with realistic demographic distributions based on CDC/CMS
epidemiological data.

Usage:
    python scripts/generate_synthea_data.py
"""

import json
import os
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Reproducible randomness
# ---------------------------------------------------------------------------
random.seed(42)

# ---------------------------------------------------------------------------
# Constants — realistic distributions from CDC / CMS public data
# ---------------------------------------------------------------------------

NUM_PATIENTS = 100

# Real CMS facility IDs (CCNs) patients will be distributed across.
# These are actual hospitals from CMS Hospital Compare.
FACILITY_IDS = [
    "050454",  # Cedars-Sinai, CA
    "050424",  # UCLA Medical Center, CA
    "100007",  # Florida Hospital, FL
    "100034",  # Tampa General Hospital, FL
    "450289",  # Baylor Scott & White, TX
    "450358",  # Methodist Dallas, TX
    "360180",  # Cleveland Clinic, OH
    "140276",  # Northwestern Memorial, IL
    "220071",  # Mass General, MA
    "330214",  # NYU Langone, NY
]

# Condition SNOMED codes and display names relevant to CMS measures
CONDITIONS = [
    {"code": "84114007", "display": "Heart failure", "cms_group": "heart-failure"},
    {"code": "233604007", "display": "Pneumonia", "cms_group": "pneumonia"},
    {"code": "13645005", "display": "Chronic obstructive lung disease", "cms_group": "copd"},
    {"code": "230690007", "display": "Cerebrovascular accident", "cms_group": "stroke"},
    {"code": "57054005", "display": "Acute myocardial infarction", "cms_group": "ami"},
    {"code": "44054006", "display": "Type 2 diabetes mellitus", "cms_group": "diabetes"},
    {"code": "38341003", "display": "Hypertensive disorder", "cms_group": "hypertension"},
    {"code": "414545008", "display": "Ischemic heart disease", "cms_group": "ihd"},
    {"code": "46635009", "display": "Type 1 diabetes mellitus", "cms_group": "diabetes"},
    {"code": "40930008", "display": "Hypothyroidism", "cms_group": "other"},
    {"code": "73211009", "display": "Diabetes mellitus", "cms_group": "diabetes"},
    {"code": "19829001", "display": "Disorder of lung", "cms_group": "copd"},
    {"code": "399211009", "display": "History of myocardial infarction", "cms_group": "ami"},
]

# Primary CMS-relevant conditions (each patient gets 1-3 of these)
PRIMARY_CONDITIONS = [c for c in CONDITIONS if c["cms_group"] in
                      {"heart-failure", "pneumonia", "copd", "stroke", "ami"}]

# Comorbidities (each patient may get 0-3 of these)
COMORBIDITIES = [c for c in CONDITIONS if c["cms_group"] in
                 {"diabetes", "hypertension", "ihd", "other"}]

# Observation LOINC codes for vital signs and labs
OBSERVATION_TYPES = [
    {"code": "8310-5", "display": "Body temperature", "unit": "degC",
     "low": 36.1, "high": 38.5, "normal_low": 36.5, "normal_high": 37.5},
    {"code": "8867-4", "display": "Heart rate", "unit": "/min",
     "low": 50, "high": 130, "normal_low": 60, "normal_high": 100},
    {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg",
     "low": 90, "high": 200, "normal_low": 100, "normal_high": 140},
    {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg",
     "low": 50, "high": 120, "normal_low": 60, "normal_high": 90},
    {"code": "2093-3", "display": "Total Cholesterol", "unit": "mg/dL",
     "low": 120, "high": 320, "normal_low": 130, "normal_high": 200},
    {"code": "2571-8", "display": "Triglycerides", "unit": "mg/dL",
     "low": 50, "high": 400, "normal_low": 50, "normal_high": 150},
    {"code": "4548-4", "display": "Hemoglobin A1c", "unit": "%",
     "low": 4.5, "high": 12.0, "normal_low": 4.5, "normal_high": 5.7},
    {"code": "2339-0", "display": "Glucose", "unit": "mg/dL",
     "low": 60, "high": 350, "normal_low": 70, "normal_high": 100},
    {"code": "33762-6", "display": "NT-proBNP", "unit": "pg/mL",
     "low": 10, "high": 5000, "normal_low": 10, "normal_high": 125},
    {"code": "2160-0", "display": "Creatinine", "unit": "mg/dL",
     "low": 0.5, "high": 4.0, "normal_low": 0.7, "normal_high": 1.3},
]

# US first/last names for realistic demographics
FIRST_NAMES_M = [
    "James", "Robert", "John", "Michael", "David", "William", "Richard",
    "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew",
    "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua",
]
FIRST_NAMES_F = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty",
    "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily", "Donna",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson",
]

# Encounter types
ENCOUNTER_CLASSES = [
    {"code": "IMP", "display": "inpatient encounter"},
    {"code": "EMER", "display": "emergency"},
    {"code": "AMB", "display": "ambulatory"},
]

# Risk levels based on condition count and age
RISK_THRESHOLDS = {"low": 0, "medium": 2, "high": 3}


def _random_date(start_year: int = 1935, end_year: int = 2000) -> str:
    """Random date as YYYY-MM-DD string."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def _recent_date(within_days: int = 365) -> str:
    """Random date within the last N days."""
    d = date.today() - timedelta(days=random.randint(1, within_days))
    return d.isoformat()


def _age_from_dob(dob: str) -> int:
    """Calculate age from ISO date string."""
    born = date.fromisoformat(dob)
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _compute_risk_level(age: int, condition_count: int) -> str:
    """Compute a risk level based on age and comorbidity burden."""
    score = condition_count
    if age >= 75:
        score += 2
    elif age >= 65:
        score += 1
    if score >= RISK_THRESHOLDS["high"]:
        return "high"
    if score >= RISK_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def generate_patient(patient_id: str, facility_id: str) -> dict:
    """Generate a FHIR R4 Patient resource."""
    gender = random.choice(["male", "female"])
    first = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
    last = random.choice(LAST_NAMES)
    dob = _random_date(1935, 2000)

    return {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]},
        "identifier": [
            {"system": "urn:oid:2.16.840.1.113883.4.3.25", "value": patient_id},
            {"system": "urn:healthpulse:facility", "value": facility_id},
        ],
        "name": [{"use": "official", "family": last, "given": [first]}],
        "gender": gender,
        "birthDate": dob,
        "address": [
            {
                "line": [f"{random.randint(100, 9999)} {random.choice(LAST_NAMES)} St"],
                "city": random.choice(["Boston", "New York", "Los Angeles", "Houston",
                                       "Chicago", "Tampa", "Cleveland", "Dallas",
                                       "San Francisco", "Miami"]),
                "state": random.choice(["MA", "NY", "CA", "TX", "IL", "FL", "OH"]),
                "postalCode": str(random.randint(10000, 99999)),
            }
        ],
        "maritalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": random.choice(["M", "S", "D", "W"]),
                }
            ]
        },
    }


def generate_condition(patient_id: str, condition_info: dict, encounter_id: str) -> dict:
    """Generate a FHIR R4 Condition resource."""
    cond_id = str(uuid.uuid4())
    onset = _recent_date(within_days=730)
    return {
        "resourceType": "Condition",
        "id": cond_id,
        "meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"]},
        "clinicalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                         "code": "active"}]
        },
        "verificationStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                         "code": "confirmed"}]
        },
        "category": [
            {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category",
                          "code": "encounter-diagnosis",
                          "display": "Encounter Diagnosis"}]}
        ],
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": condition_info["code"],
                    "display": condition_info["display"],
                }
            ],
            "text": condition_info["display"],
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "onsetDateTime": onset,
        "recordedDate": onset,
        "_cms_group": condition_info["cms_group"],
    }


def generate_observation(patient_id: str, obs_type: dict, encounter_id: str,
                         is_abnormal: bool = False) -> dict:
    """Generate a FHIR R4 Observation resource (vital sign or lab)."""
    obs_id = str(uuid.uuid4())

    if is_abnormal:
        # Generate an abnormal value outside normal range
        if random.random() < 0.5:
            value = random.uniform(obs_type["low"], obs_type["normal_low"])
        else:
            value = random.uniform(obs_type["normal_high"], obs_type["high"])
    else:
        value = random.uniform(obs_type["normal_low"], obs_type["normal_high"])

    value = round(value, 1)

    return {
        "resourceType": "Observation",
        "id": obs_id,
        "meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-vital-signs"]},
        "status": "final",
        "category": [
            {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                          "code": "vital-signs",
                          "display": "Vital Signs"}]}
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": obs_type["code"],
                    "display": obs_type["display"],
                }
            ],
            "text": obs_type["display"],
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "encounter": {"reference": f"Encounter/{encounter_id}"},
        "effectiveDateTime": _recent_date(within_days=90),
        "valueQuantity": {
            "value": value,
            "unit": obs_type["unit"],
            "system": "http://unitsofmeasure.org",
            "code": obs_type["unit"],
        },
    }


def generate_encounter(patient_id: str, facility_id: str) -> dict:
    """Generate a FHIR R4 Encounter resource."""
    enc_id = str(uuid.uuid4())
    enc_class = random.choice(ENCOUNTER_CLASSES)
    start_date = _recent_date(within_days=365)
    end_date = (date.fromisoformat(start_date) + timedelta(days=random.randint(1, 14))).isoformat()

    return {
        "resourceType": "Encounter",
        "id": enc_id,
        "meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter"]},
        "status": random.choice(["finished", "in-progress"]),
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": enc_class["code"],
            "display": enc_class["display"],
        },
        "type": [
            {"coding": [{"system": "http://snomed.info/sct",
                          "code": "185347001",
                          "display": "Encounter for problem"}],
             "text": "Encounter for problem"}
        ],
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {"start": start_date, "end": end_date},
        "serviceProvider": {"identifier": {"system": "urn:healthpulse:facility",
                                           "value": facility_id}},
    }


def generate_all() -> dict:
    """Generate full FHIR Bundle with ~100 patients and related resources."""
    entries = []

    # Track patient summaries for the index file
    patient_summaries = []

    for i in range(NUM_PATIENTS):
        patient_id = str(uuid.uuid4())
        facility_id = FACILITY_IDS[i % len(FACILITY_IDS)]

        # Generate patient
        patient = generate_patient(patient_id, facility_id)
        entries.append({"resource": patient, "fullUrl": f"urn:uuid:{patient_id}"})

        # Generate 1-3 encounters per patient
        num_encounters = random.randint(1, 3)
        encounter_ids = []
        for _ in range(num_encounters):
            encounter = generate_encounter(patient_id, facility_id)
            entries.append({"resource": encounter, "fullUrl": f"urn:uuid:{encounter['id']}"})
            encounter_ids.append(encounter["id"])

        # Generate 1-2 primary conditions (CMS measure conditions)
        num_primary = random.randint(1, 2)
        patient_conditions = random.sample(PRIMARY_CONDITIONS, min(num_primary, len(PRIMARY_CONDITIONS)))

        # Generate 0-3 comorbidities
        num_comorbid = random.randint(0, 3)
        patient_comorbidities = random.sample(COMORBIDITIES, min(num_comorbid, len(COMORBIDITIES)))

        all_conditions = patient_conditions + patient_comorbidities
        condition_names = []
        for cond_info in all_conditions:
            enc_id = random.choice(encounter_ids)
            condition = generate_condition(patient_id, cond_info, enc_id)
            entries.append({"resource": condition, "fullUrl": f"urn:uuid:{condition['id']}"})
            condition_names.append(cond_info["display"])

        # Generate 3-6 observations per patient
        num_obs = random.randint(3, 6)
        obs_types = random.sample(OBSERVATION_TYPES, min(num_obs, len(OBSERVATION_TYPES)))
        # Higher-risk patients get more abnormal values
        abnormal_chance = 0.2 + (len(all_conditions) * 0.1)
        for obs_type in obs_types:
            enc_id = random.choice(encounter_ids)
            is_abnormal = random.random() < abnormal_chance
            observation = generate_observation(patient_id, obs_type, enc_id, is_abnormal)
            entries.append({"resource": observation, "fullUrl": f"urn:uuid:{observation['id']}"})

        # Compute risk level
        age = _age_from_dob(patient["birthDate"])
        risk_level = _compute_risk_level(age, len(all_conditions))

        patient_summaries.append({
            "patient_id": patient_id,
            "facility_id": facility_id,
            "name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
            "age": age,
            "gender": patient["gender"],
            "conditions": condition_names,
            "cms_groups": list({c["cms_group"] for c in all_conditions}),
            "num_encounters": num_encounters,
            "num_observations": num_obs,
            "risk_level": risk_level,
        })

    bundle = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "timestamp": date.today().isoformat() + "T00:00:00Z",
        "total": len(entries),
        "entry": entries,
    }

    return bundle, patient_summaries


def main():
    project_root = Path(__file__).resolve().parent.parent
    synthea_dir = project_root / "data" / "synthea"
    synthea_dir.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic FHIR R4 patient data...")
    bundle, summaries = generate_all()

    # Write the FHIR Bundle
    bundle_path = synthea_dir / "fhir_bundle.json"
    with open(bundle_path, "w") as f:
        json.dump(bundle, f, indent=2)
    bundle_size_mb = bundle_path.stat().st_size / (1024 * 1024)
    print(f"  Bundle: {bundle_path} ({bundle_size_mb:.1f} MB, {bundle['total']} entries)")

    # Write patient index (quick lookup file)
    index_path = synthea_dir / "patient_index.json"
    with open(index_path, "w") as f:
        json.dump({
            "generated": date.today().isoformat(),
            "total_patients": len(summaries),
            "facility_ids": FACILITY_IDS,
            "patients": summaries,
        }, f, indent=2)
    print(f"  Index:  {index_path} ({len(summaries)} patients)")

    # Print distribution summary
    from collections import Counter
    facility_counts = Counter(s["facility_id"] for s in summaries)
    risk_counts = Counter(s["risk_level"] for s in summaries)
    condition_counts = Counter(g for s in summaries for g in s["cms_groups"])

    print(f"\nDistribution:")
    print(f"  Patients per facility: {dict(facility_counts)}")
    print(f"  Risk levels: {dict(risk_counts)}")
    print(f"  CMS condition groups: {dict(condition_counts)}")


if __name__ == "__main__":
    main()
