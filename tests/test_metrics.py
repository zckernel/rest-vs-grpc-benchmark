import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.metrics import compute_metrics


def test_avg():
    r = compute_metrics([1.0, 2.0, 3.0, 4.0, 5.0], total_seconds=5.0, errors=0)
    assert r.avg_ms == pytest.approx(3.0)

def test_percentile_order():
    import random; random.seed(0)
    lats = [random.uniform(1, 100) for _ in range(1000)]
    r = compute_metrics(lats, total_seconds=10.0, errors=0)
    assert r.p50_ms <= r.p95_ms <= r.p99_ms

def test_throughput():
    r = compute_metrics([1.0] * 100, total_seconds=10.0, errors=0)
    assert r.throughput_rps == pytest.approx(10.0)

def test_error_rate():
    r = compute_metrics([1.0] * 90, total_seconds=1.0, errors=10)
    assert r.error_rate == pytest.approx(10.0)

def test_empty_raises():
    with pytest.raises(ValueError):
        compute_metrics([], total_seconds=1.0, errors=0)
