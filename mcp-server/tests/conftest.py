"""Shared pytest fixtures for HealthPulse MCP tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from healthpulse_mcp.domo_client import DomoClient


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
    """Sample facility rows."""
    return [
        {
            "facility_id": "100001",
            "facility_name": "General Hospital A",
            "state": "CA",
            "city": "Los Angeles",
            "zip_code": "90001",
            "hospital_type": "Acute Care Hospitals",
            "overall_rating": "4",
            "emergency_services": "Yes",
            "county_fips": "06037",
        },
        {
            "facility_id": "100002",
            "facility_name": "City Medical Center",
            "state": "CA",
            "city": "San Francisco",
            "zip_code": "94102",
            "hospital_type": "Acute Care Hospitals",
            "overall_rating": "3",
            "emergency_services": "Yes",
            "county_fips": "06075",
        },
        {
            "facility_id": "100003",
            "facility_name": "Rural Health Clinic",
            "state": "CA",
            "city": "Fresno",
            "zip_code": "93701",
            "hospital_type": "Critical Access Hospitals",
            "overall_rating": "2",
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
