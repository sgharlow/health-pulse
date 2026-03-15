"""Z-score computation and anomaly detection for healthcare quality metrics."""

import math
from typing import Any, Optional


def compute_z_scores(
    values: list[float],
    labels: Optional[list[str]] = None,
) -> list[float]:
    """Compute Z-scores for a list of numeric values."""
    n = len(values)
    if n < 2:
        return [0.0] * n
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance) if variance > 0 else 1.0
    return [(x - mean) / std for x in values]


def classify_severity(z_score: float) -> Optional[str]:
    """Classify anomaly severity based on absolute Z-score."""
    abs_z = abs(z_score)
    if abs_z >= 3.0:
        return "critical"
    elif abs_z >= 2.5:
        return "high"
    elif abs_z >= 2.0:
        return "medium"
    return None


def detect_anomalies(
    data: list[dict[str, Any]],
    score_key: str = "score",
    threshold: float = 2.0,
) -> list[dict[str, Any]]:
    """Detect anomalies in a list of facility/measure data."""
    scored = []
    for item in data:
        try:
            val = float(item[score_key])
            scored.append((item, val))
        except (ValueError, TypeError, KeyError):
            continue

    if len(scored) < 2:
        return []

    values = [v for _, v in scored]
    z_scores = compute_z_scores(values)

    anomalies = []
    for (item, _val), z in zip(scored, z_scores):
        severity = classify_severity(z)
        if severity and abs(z) >= threshold:
            anomalies.append({
                **item,
                "z_score": round(z, 2),
                "severity": severity,
            })

    severity_order = {"critical": 0, "high": 1, "medium": 2}
    anomalies.sort(key=lambda x: severity_order.get(x["severity"], 99))
    return anomalies
