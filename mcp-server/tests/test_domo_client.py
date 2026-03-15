"""Tests for Domo API client."""

import responses
from healthpulse_mcp.domo_client import DomoClient


@responses.activate
def test_get_token_uses_get_request():
    """Domo OAuth uses GET (not POST) - non-standard."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "test-token", "token_type": "bearer", "expires_in": 3600},
    )
    client = DomoClient("test-id", "test-secret")
    token = client.get_token()
    assert token == "test-token"
    assert responses.calls[0].request.method == "GET"


@responses.activate
def test_token_caching():
    """Token should be cached and not re-fetched within TTL."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "cached-token", "token_type": "bearer", "expires_in": 3600},
    )
    client = DomoClient("test-id", "test-secret")
    token1 = client.get_token()
    token2 = client.get_token()
    assert token1 == token2
    assert len(responses.calls) == 1


@responses.activate
def test_query_dataset():
    """Test SQL query execution against Domo dataset."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "t", "token_type": "bearer", "expires_in": 3600},
    )
    responses.add(
        responses.POST,
        "https://api.domo.com/v1/datasets/query/execute/ds-123",
        json={"columns": ["name", "score"], "rows": [["Hospital A", "12.5"]], "numRows": 1},
    )
    client = DomoClient("test-id", "test-secret")
    result = client.query("ds-123", "SELECT name, score FROM table LIMIT 1")
    assert result["numRows"] == 1
    assert result["columns"] == ["name", "score"]


@responses.activate
def test_query_returns_dicts():
    """Test helper that zips columns + rows into dicts."""
    responses.add(
        responses.GET,
        "https://api.domo.com/oauth/token",
        json={"access_token": "t", "token_type": "bearer", "expires_in": 3600},
    )
    responses.add(
        responses.POST,
        "https://api.domo.com/v1/datasets/query/execute/ds-123",
        json={"columns": ["id", "val"], "rows": [["1", "a"], ["2", "b"]], "numRows": 2},
    )
    client = DomoClient("test-id", "test-secret")
    rows = client.query_as_dicts("ds-123", "SELECT id, val FROM table")
    assert rows == [{"id": "1", "val": "a"}, {"id": "2", "val": "b"}]
