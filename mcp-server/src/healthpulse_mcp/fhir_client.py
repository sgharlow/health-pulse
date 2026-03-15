"""Lightweight FHIR data layer for Synthea synthetic patient data.

Loads FHIR R4 Bundle JSON files from disk and provides indexed query
methods.  This avoids the need for a full HAPI FHIR server or Docker
while still demonstrating real synthetic patient data in the MCP tools.

No external dependencies — uses only stdlib (json, pathlib).
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default data directory relative to project root
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "synthea"


class FHIRDataStore:
    """In-memory FHIR data store loaded from Synthea Bundle JSON.

    Indexes patients, conditions, observations, and encounters by
    patient ID and facility ID for fast lookup.
    """

    def __init__(self, data_dir: Optional[str | Path] = None):
        self._data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        self._patients: dict[str, dict] = {}
        self._conditions: dict[str, list[dict]] = {}  # patient_id -> [conditions]
        self._observations: dict[str, list[dict]] = {}  # patient_id -> [observations]
        self._encounters: dict[str, list[dict]] = {}  # patient_id -> [encounters]
        self._facility_patients: dict[str, list[str]] = {}  # facility_id -> [patient_ids]
        self._patient_facility: dict[str, str] = {}  # patient_id -> facility_id
        self._patient_index: list[dict] = []  # summaries from patient_index.json
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def patient_count(self) -> int:
        return len(self._patients)

    def load(self) -> None:
        """Load and index FHIR data from disk.

        Reads both the full FHIR Bundle and the patient index file.
        Idempotent — calling multiple times re-indexes from disk.
        """
        self._patients.clear()
        self._conditions.clear()
        self._observations.clear()
        self._encounters.clear()
        self._facility_patients.clear()
        self._patient_facility.clear()
        self._patient_index.clear()

        # Load patient index (lightweight summary)
        index_path = self._data_dir / "patient_index.json"
        if index_path.exists():
            with open(index_path, "r") as f:
                index_data = json.load(f)
            self._patient_index = index_data.get("patients", [])
            # Build facility -> patient_id mapping from index
            for summary in self._patient_index:
                pid = summary["patient_id"]
                fid = summary["facility_id"]
                self._patient_facility[pid] = fid
                self._facility_patients.setdefault(fid, []).append(pid)

        # Load full FHIR Bundle
        bundle_path = self._data_dir / "fhir_bundle.json"
        if bundle_path.exists():
            with open(bundle_path, "r") as f:
                bundle = json.load(f)
            self._index_bundle(bundle)
        else:
            logger.warning("FHIR bundle not found at %s", bundle_path)

        self._loaded = True
        logger.info(
            "FHIR data loaded: %d patients, %d facilities",
            len(self._patients),
            len(self._facility_patients),
        )

    def _index_bundle(self, bundle: dict) -> None:
        """Index all resources from a FHIR Bundle by type and patient."""
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            rtype = resource.get("resourceType")
            rid = resource.get("id", "")

            if rtype == "Patient":
                self._patients[rid] = resource
                # Extract facility from identifier
                for ident in resource.get("identifier", []):
                    if ident.get("system") == "urn:healthpulse:facility":
                        fid = ident["value"]
                        self._patient_facility[rid] = fid
                        self._facility_patients.setdefault(fid, []).append(rid)

            elif rtype == "Condition":
                pid = self._extract_patient_id(resource)
                if pid:
                    self._conditions.setdefault(pid, []).append(resource)

            elif rtype == "Observation":
                pid = self._extract_patient_id(resource)
                if pid:
                    self._observations.setdefault(pid, []).append(resource)

            elif rtype == "Encounter":
                pid = self._extract_patient_id(resource)
                if pid:
                    self._encounters.setdefault(pid, []).append(resource)

    @staticmethod
    def _extract_patient_id(resource: dict) -> Optional[str]:
        """Extract patient ID from a resource's subject reference."""
        ref = resource.get("subject", {}).get("reference", "")
        if ref.startswith("Patient/"):
            return ref[len("Patient/"):]
        return None

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_patient(self, patient_id: str) -> Optional[dict]:
        """Return a single Patient resource by ID, or None."""
        self._ensure_loaded()
        return self._patients.get(patient_id)

    def get_patient_summary(self, patient_id: str) -> Optional[dict]:
        """Return the patient index summary (with risk level, conditions list)."""
        self._ensure_loaded()
        for summary in self._patient_index:
            if summary["patient_id"] == patient_id:
                return summary
        return None

    def search_patients(self, facility_id: str) -> list[dict]:
        """Return all patient summaries for a given facility ID."""
        self._ensure_loaded()
        patient_ids = self._facility_patients.get(facility_id, [])
        return [
            s for s in self._patient_index
            if s["patient_id"] in set(patient_ids)
        ]

    def get_conditions(self, patient_id: str) -> list[dict]:
        """Return all Condition resources for a patient."""
        self._ensure_loaded()
        return self._conditions.get(patient_id, [])

    def get_observations(self, patient_id: str) -> list[dict]:
        """Return all Observation resources for a patient."""
        self._ensure_loaded()
        return self._observations.get(patient_id, [])

    def get_encounters(self, patient_id: str) -> list[dict]:
        """Return all Encounter resources for a patient."""
        self._ensure_loaded()
        return self._encounters.get(patient_id, [])

    def get_facility_id(self, patient_id: str) -> Optional[str]:
        """Return the facility ID a patient is assigned to."""
        self._ensure_loaded()
        return self._patient_facility.get(patient_id)

    def get_facility_ids(self) -> list[str]:
        """Return all facility IDs that have patients."""
        self._ensure_loaded()
        return list(self._facility_patients.keys())

    def get_patients_by_condition(
        self, facility_id: str, cms_group: str
    ) -> list[dict]:
        """Return patient summaries at a facility with a specific CMS condition group."""
        self._ensure_loaded()
        patients = self.search_patients(facility_id)
        return [p for p in patients if cms_group in p.get("cms_groups", [])]

    def get_patients_by_risk(
        self, facility_id: str, risk_level: str
    ) -> list[dict]:
        """Return patient summaries at a facility with a specific risk level."""
        self._ensure_loaded()
        patients = self.search_patients(facility_id)
        return [p for p in patients if p.get("risk_level") == risk_level]

    def get_cohort_stats(
        self, facility_id: str, cms_group: Optional[str] = None
    ) -> dict[str, Any]:
        """Compute cohort statistics for patients at a facility.

        Returns:
            dict with patient_count, avg_age, gender_split, risk_distribution,
            common_comorbidities, and condition_distribution.
        """
        self._ensure_loaded()
        patients = self.search_patients(facility_id)
        if cms_group:
            patients = [p for p in patients if cms_group in p.get("cms_groups", [])]

        if not patients:
            return {
                "patient_count": 0,
                "facility_id": facility_id,
                "condition_filter": cms_group,
            }

        ages = [p["age"] for p in patients]
        genders = [p["gender"] for p in patients]
        risks = [p["risk_level"] for p in patients]

        # Count all conditions across cohort
        all_conditions: dict[str, int] = {}
        for p in patients:
            for cond in p.get("conditions", []):
                all_conditions[cond] = all_conditions.get(cond, 0) + 1

        # Count CMS groups
        all_groups: dict[str, int] = {}
        for p in patients:
            for g in p.get("cms_groups", []):
                all_groups[g] = all_groups.get(g, 0) + 1

        # Find patients with 2+ comorbidities
        multi_comorbid = sum(1 for p in patients if len(p.get("conditions", [])) >= 3)

        return {
            "patient_count": len(patients),
            "facility_id": facility_id,
            "condition_filter": cms_group,
            "avg_age": round(sum(ages) / len(ages), 1),
            "age_range": {"min": min(ages), "max": max(ages)},
            "gender_split": {
                "male": sum(1 for g in genders if g == "male"),
                "female": sum(1 for g in genders if g == "female"),
            },
            "risk_distribution": {
                "high": sum(1 for r in risks if r == "high"),
                "medium": sum(1 for r in risks if r == "medium"),
                "low": sum(1 for r in risks if r == "low"),
            },
            "patients_with_2plus_comorbidities": multi_comorbid,
            "comorbidity_rate": round(multi_comorbid / len(patients), 2) if patients else 0,
            "common_conditions": dict(
                sorted(all_conditions.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "cms_group_distribution": dict(
                sorted(all_groups.items(), key=lambda x: x[1], reverse=True)
            ),
        }

    def _ensure_loaded(self) -> None:
        """Lazy-load data if not already loaded."""
        if not self._loaded:
            self.load()


# Module-level singleton
fhir_store = FHIRDataStore()
