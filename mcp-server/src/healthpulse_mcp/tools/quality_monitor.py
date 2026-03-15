"""Quality monitor tool — detects statistical anomalies in CMS quality measures."""

import os
from typing import Any

from healthpulse_mcp.analytics import detect_anomalies
from healthpulse_mcp.domo_client import DomoClient
from healthpulse_mcp.validation import validate_state

# Maps measure_group to CMS measure ID prefixes
MEASURE_GROUP_PREFIXES: dict[str, list[str]] = {
    "mortality": ["MORT_"],
    "readmission": ["READM_"],
    "safety": ["PSI_", "HAI_", "COMP_"],
    "timeliness": ["OP_", "ED_", "IMM_"],
    "all": [],  # empty means no filter
}


async def run(domo: DomoClient, args: dict[str, Any]) -> dict[str, Any]:
    """Detect statistical anomalies in CMS quality measures.

    Args:
        domo: Authenticated DomoClient
        args: Tool arguments with keys:
            state (str, optional): Two-letter state code filter
            measure_group (str): One of mortality|readmission|safety|timeliness|all
            threshold_sigma (float): Z-score threshold for anomaly detection (default 2.0)

    Returns:
        dict with total_facilities_analyzed, measures_checked, anomaly_count, anomalies, filters
    """
    dataset_id = os.environ.get("HP_QUALITY_DATASET_ID")
    if not dataset_id:
        return {"error": "HP_QUALITY_DATASET_ID environment variable not set"}

    state = validate_state(args.get("state"))
    measure_group = args.get("measure_group", "all")
    threshold_sigma = float(args.get("threshold_sigma", 2.0))

    # Quality dataset does NOT have 'state' or 'facility_name'.
    # If a state filter is requested, query facilities first to get facility_ids in that state,
    # then filter quality data in Python.
    quality_facility_ids: set[str] | None = None
    if state:
        facilities_id = os.environ.get("HP_FACILITIES_DATASET_ID")
        if not facilities_id:
            return {"error": "HP_FACILITIES_DATASET_ID environment variable not set (required for state filter)"}
        try:
            fac_sql = f"SELECT facility_id FROM table WHERE state = '{state}'"
            fac_rows = domo.query_as_dicts(facilities_id, fac_sql)
            quality_facility_ids = {str(r.get("facility_id")) for r in fac_rows}
        except Exception as exc:
            return {"error": f"Facilities query failed: {exc}"}

    # Query quality dataset — only columns that exist in the actual schema
    sql = "SELECT facility_id, measure_id, measure_name, score, compared_to_national FROM table"

    try:
        rows = domo.query_as_dicts(dataset_id, sql)
    except Exception as exc:
        return {"error": f"Query failed: {exc}"}

    # Apply state filter in Python when needed
    if quality_facility_ids is not None:
        rows = [r for r in rows if str(r.get("facility_id")) in quality_facility_ids]

    # Filter by measure group
    prefixes = MEASURE_GROUP_PREFIXES.get(measure_group, [])
    if prefixes:
        rows = [
            r for r in rows
            if any(str(r.get("measure_id", "")).upper().startswith(p) for p in prefixes)
        ]

    # Group by measure_id and run anomaly detection per measure
    measures: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        mid = str(row.get("measure_id", "UNKNOWN"))
        measures.setdefault(mid, []).append(row)

    all_anomalies: list[dict[str, Any]] = []
    for mid, measure_rows in measures.items():
        anomalies = detect_anomalies(measure_rows, score_key="score", threshold=threshold_sigma)
        all_anomalies.extend(anomalies)

    # Sort by severity order then z_score magnitude
    severity_order = {"critical": 0, "high": 1, "medium": 2}
    all_anomalies.sort(
        key=lambda x: (severity_order.get(x.get("severity", ""), 99), -abs(x.get("z_score", 0)))
    )

    facility_ids = {str(r.get("facility_id")) for r in rows}

    return {
        "total_facilities_analyzed": len(facility_ids),
        "measures_checked": len(measures),
        "anomaly_count": len(all_anomalies),
        "anomalies": all_anomalies[:20],
        "filters": {
            "state": state,
            "measure_group": measure_group,
            "threshold_sigma": threshold_sigma,
        },
    }
