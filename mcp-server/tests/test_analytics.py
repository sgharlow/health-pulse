"""Tests for analytics engine."""

from healthpulse_mcp.analytics import compute_z_scores, classify_severity, detect_anomalies


def test_compute_z_scores_basic():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    z_scores = compute_z_scores(values)
    assert len(z_scores) == 5
    assert abs(z_scores[2]) < 0.01


def test_compute_z_scores_outlier():
    values = [10.0, 20.0, 100.0]
    z_scores = compute_z_scores(values)
    assert z_scores[2] > 1.0


def test_classify_severity_critical():
    assert classify_severity(3.5) == "critical"


def test_classify_severity_high():
    assert classify_severity(2.7) == "high"


def test_classify_severity_medium():
    assert classify_severity(2.1) == "medium"


def test_classify_severity_normal():
    assert classify_severity(1.5) is None


def test_detect_anomalies():
    # Need enough clustered values so the outlier exceeds z=2.0
    data = [
        {"facility": "A", "measure": "MORT", "score": 10.0},
        {"facility": "B", "measure": "MORT", "score": 11.0},
        {"facility": "D", "measure": "MORT", "score": 10.0},
        {"facility": "E", "measure": "MORT", "score": 11.0},
        {"facility": "F", "measure": "MORT", "score": 10.0},
        {"facility": "G", "measure": "MORT", "score": 11.0},
        {"facility": "C", "measure": "MORT", "score": 50.0},
    ]
    anomalies = detect_anomalies(data, score_key="score", threshold=2.0)
    assert len(anomalies) == 1
    assert anomalies[0]["facility"] == "C"
    assert anomalies[0]["severity"] in ("medium", "high", "critical")
    assert "z_score" in anomalies[0]


def test_detect_anomalies_skips_non_numeric():
    data = [
        {"facility": "A", "score": "Not Available"},
        {"facility": "B", "score": 10.0},
        {"facility": "C", "score": 12.0},
    ]
    anomalies = detect_anomalies(data, score_key="score", threshold=2.0)
    assert isinstance(anomalies, list)


def test_detect_anomalies_empty():
    assert detect_anomalies([], threshold=2.0) == []
