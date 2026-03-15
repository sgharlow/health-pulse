"""Domo API client with OAuth token caching and SQL query execution."""

import base64
import time
from typing import Any, Optional

import requests


class DomoClient:
    """Wraps Domo REST API with token caching."""

    API_BASE = "https://api.domo.com"
    TOKEN_BUFFER_SECONDS = 60

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0

    def get_token(self) -> str:
        """Get OAuth token, using cache if valid."""
        now = time.time()
        if self._cached_token and now < self._token_expires_at - self.TOKEN_BUFFER_SECONDS:
            return self._cached_token

        basic = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()
        resp = requests.get(
            f"{self.API_BASE}/oauth/token",
            params={"grant_type": "client_credentials", "scope": "data"},
            headers={"Authorization": f"Basic {basic}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._cached_token = data["access_token"]
        self._token_expires_at = now + data.get("expires_in", 3600)
        return self._cached_token

    def query(self, dataset_id: str, sql: str) -> dict[str, Any]:
        """Execute SQL query against a Domo dataset. Returns raw response."""
        token = self.get_token()
        resp = requests.post(
            f"{self.API_BASE}/v1/datasets/query/execute/{dataset_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"sql": sql},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    def query_as_dicts(self, dataset_id: str, sql: str) -> list[dict[str, Any]]:
        """Execute SQL and return results as list of dicts."""
        result = self.query(dataset_id, sql)
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        return [dict(zip(columns, row)) for row in rows]

    def get_dataset_info(self, dataset_id: str) -> dict[str, Any]:
        """Get dataset metadata (name, schema, row count)."""
        token = self.get_token()
        resp = requests.get(
            f"{self.API_BASE}/v1/datasets/{dataset_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
