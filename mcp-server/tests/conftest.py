"""Shared pytest fixtures for HealthPulse MCP tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from healthpulse_mcp.cache import tool_cache
from healthpulse_mcp.domo_client import DomoClient


@pytest.fixture(autouse=True)
def _clear_tool_cache():
    """Clear the module-level tool result cache before every test.

    This prevents cached results from one test leaking into another.
    """
    tool_cache.clear()
    yield
    tool_cache.clear()


@pytest.fixture
def mock_domo():
    """Return a MagicMock DomoClient with query_as_dicts stubbed."""
    domo = MagicMock(spec=DomoClient)
    domo.query_as_dicts = MagicMock(return_value=[])
    return domo


@pytest.fixture
def sample_quality_rows():
    """Sample quality measure rows representative of CMS data."""
    return [
        {
            "facility_id": "100001",
            "facility_name": "General Hospital A",
            "state": "CA",
            "measure_id": "MORT_30_AMI",
            "score": "14.5",
            "compared_to_national": "No Different Than the National Rate",
        },
        {
            "facility_id": "100002",
            "facility_name": "City Medical Center",
            "state": "CA",
            "measure_id": "MORT_30_AMI",
            "score": "15.1",
            "compared_to_national": "No Different Than the National Rate",
        },
        {
            "facility_id": "100003",
            "facility_name": "Rural Health Clinic",
            "state": "CA",
            "measure_id": "MORT_30_AMI",
            "score": "14.8",
            "compared_to_national": "No Different Than the National Rate",
        },
        {
            "facility_id": "100004",
            "facility_name": "Memorial Hospital",
            "state": "CA",
            "measure_id": "MORT_30_AMI",
            "score": "14.9",
            "compared_to_national": "No Different Than the National Rate",
        },
        {
            "facility_id": "100005",
            "facility_name": "Outlier Regional",
            "state": "CA",
            "measure_id": "MORT_30_AMI",
            "score": "25.0",
            "compared_to_national": "Worse Than the National Rate",
        },
        {
            "facility_id": "100006",
            "facility_name": "Valley Hospital",
            "state": "CA",
            "measure_id": "READM_30_AMI",
            "score": "16.2",
            "compared_to_national": "No Different Than the National Rate",
        },
    ]


@pytest.fixture
def sample_readmission_rows():
    """Sample readmission measure rows."""
    return [
        {
            "facility_id": "100001",
            "facility_name": "General Hospital A",
            "state": "CA",
            "measure_id": "READM_30_AMI",
            "excess_readmission_ratio": "1.02",
            "number_of_readmissions": "45",
            "predicted_readmission_rate": "18.5",
        },
        {
            "facility_id": "100002",
            "facility_name": "City Medical Center",
            "state": "CA",
            "measure_id": "READM_30_AMI",
            "excess_readmission_ratio": "1.15",
            "number_of_readmissions": "72",
            "predicted_readmission_rate": "19.8",
        },
        {
            "facility_id": "100003",
            "facility_name": "Rural Health Clinic",
            "state": "CA",
            "measure_id": "READM_30_HF",
            "excess_readmission_ratio": "1.08",
            "number_of_readmissions": "30",
            "predicted_readmission_rate": "22.1",
        },
    ]


@pytest.fixture
def sample_facilities_rows():
    """Sample facility rows matching actual Domo HP_FACILITIES_DATASET_ID column names."""
    return [
        {
            "facility_id": "100001",
            "facility_name": "General Hospital A",
            "state": "CA",
            "city_town": "Los Angeles",
            "zip_code": "90001",
            "hospital_type": "Acute Care Hospitals",
            "hospital_overall_rating": "4",
            "emergency_services": "Yes",
            "county_fips": "06037",
        },
        {
            "facility_id": "100002",
            "facility_name": "City Medical Center",
            "state": "CA",
            "city_town": "San Francisco",
            "zip_code": "94102",
            "hospital_type": "Acute Care Hospitals",
            "hospital_overall_rating": "3",
            "emergency_services": "Yes",
            "county_fips": "06075",
        },
        {
            "facility_id": "100003",
            "facility_name": "Rural Health Clinic",
            "state": "CA",
            "city_town": "Fresno",
            "zip_code": "93701",
            "hospital_type": "Critical Access Hospitals",
            "hospital_overall_rating": "2",
            "emergency_services": "Yes",
            "county_fips": "06019",
        },
    ]


@pytest.fixture
def sample_svi_rows():
    """Sample community SVI rows."""
    return [
        {"county_fips": "06037", "county_name": "Los Angeles", "state": "CA", "svi_score": "0.82"},
        {"county_fips": "06075", "county_name": "San Francisco", "state": "CA", "svi_score": "0.45"},
        {"county_fips": "06019", "county_name": "Fresno", "state": "CA", "svi_score": "0.91"},
    ]


@pytest.fixture
def sample_experience_rows():
    """Sample HCAHPS patient experience rows matching actual Domo hp_patient_experience columns.

    Real column names: facility_id, hcahps_measure_id, hcahps_question,
    patient_survey_star_rating, hcahps_answer_percent, number_of_completed_surveys,
    start_date, end_date.

    patient_survey_star_rating can be "Not Applicable" for individual measure rows.
    """
    return [
        # Communication measures — facility 100001
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_COMP_1_A_P",
            "hcahps_question": "Patients who reported that their nurses \"Always\" communicated well",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "78",
            "number_of_completed_surveys": "300",
        },
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_COMP_2_A_P",
            "hcahps_question": "Patients who reported that their doctors \"Always\" communicated well",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "72",
            "number_of_completed_surveys": "300",
        },
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_COMP_3_A_P",
            "hcahps_question": "Patients who reported that they \"Always\" received help as soon as they wanted",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "65",
            "number_of_completed_surveys": "300",
        },
        # Responsiveness
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_COMP_5_A_P",
            "hcahps_question": "Patients who reported that staff \"Always\" explained about medicines",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "55",
            "number_of_completed_surveys": "300",
        },
        # Environment
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_CLEAN_HSP_A_P",
            "hcahps_question": "Patients who reported that their room and bathroom were \"Always\" clean",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "68",
            "number_of_completed_surveys": "300",
        },
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_QUIET_HSP_A_P",
            "hcahps_question": "Patients who reported that the area around their room was \"Always\" quiet at night",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "58",
            "number_of_completed_surveys": "300",
        },
        # Overall
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_HSP_RATING_9_10",
            "hcahps_question": "Patients who gave their hospital a rating of 9 or 10 on a scale from 0 to 10",
            "patient_survey_star_rating": "4",
            "hcahps_answer_percent": "70",
            "number_of_completed_surveys": "300",
        },
        {
            "facility_id": "100001",
            "hcahps_measure_id": "H_RECMND_DY",
            "hcahps_question": "Patients who reported YES they would definitely recommend the hospital",
            "patient_survey_star_rating": "4",
            "hcahps_answer_percent": "71",
            "number_of_completed_surveys": "300",
        },
        # Second facility — worse scores
        {
            "facility_id": "100002",
            "hcahps_measure_id": "H_COMP_1_A_P",
            "hcahps_question": "Patients who reported that their nurses \"Always\" communicated well",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "2",
            "number_of_completed_surveys": "150",
        },
        {
            "facility_id": "100002",
            "hcahps_measure_id": "H_COMP_2_A_P",
            "hcahps_question": "Patients who reported that their doctors \"Always\" communicated well",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "1",
            "number_of_completed_surveys": "150",
        },
        {
            "facility_id": "100002",
            "hcahps_measure_id": "H_COMP_5_A_P",
            "hcahps_question": "Patients who reported that staff \"Always\" explained about medicines",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "1",
            "number_of_completed_surveys": "150",
        },
        {
            "facility_id": "100002",
            "hcahps_measure_id": "H_CLEAN_HSP_A_P",
            "hcahps_question": "Patients who reported that their room and bathroom were \"Always\" clean",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "2",
            "number_of_completed_surveys": "150",
        },
        {
            "facility_id": "100002",
            "hcahps_measure_id": "H_HSP_RATING_9_10",
            "hcahps_question": "Patients who gave their hospital a rating of 9 or 10 on a scale from 0 to 10",
            "patient_survey_star_rating": "2",
            "hcahps_answer_percent": "2",
            "number_of_completed_surveys": "150",
        },
        # Third facility — good scores
        {
            "facility_id": "100003",
            "hcahps_measure_id": "H_COMP_1_A_P",
            "hcahps_question": "Patients who reported that their nurses \"Always\" communicated well",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "90",
            "number_of_completed_surveys": "500",
        },
        {
            "facility_id": "100003",
            "hcahps_measure_id": "H_COMP_5_A_P",
            "hcahps_question": "Patients who reported that staff \"Always\" explained about medicines",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "88",
            "number_of_completed_surveys": "500",
        },
        {
            "facility_id": "100003",
            "hcahps_measure_id": "H_CLEAN_HSP_A_P",
            "hcahps_question": "Patients who reported that their room and bathroom were \"Always\" clean",
            "patient_survey_star_rating": "Not Applicable",
            "hcahps_answer_percent": "82",
            "number_of_completed_surveys": "500",
        },
        {
            "facility_id": "100003",
            "hcahps_measure_id": "H_HSP_RATING_9_10",
            "hcahps_question": "Patients who gave their hospital a rating of 9 or 10 on a scale from 0 to 10",
            "patient_survey_star_rating": "5",
            "hcahps_answer_percent": "92",
            "number_of_completed_surveys": "500",
        },
    ]
