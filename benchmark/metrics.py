from dataclasses import dataclass


@dataclass
class MetricsResult:
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    throughput_rps: float
    errors: int
    error_rate: float  # percent


def _percentile(s: list[float], p: float) -> float:
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def compute_metrics(latencies: list[float], total_seconds: float, errors: int) -> MetricsResult:
    if not latencies:
        raise ValueError("no latency samples")
    s = sorted(latencies)
    total = len(s) + errors
    return MetricsResult(
        avg_ms=sum(s) / len(s),
        p50_ms=_percentile(s, 50),
        p95_ms=_percentile(s, 95),
        p99_ms=_percentile(s, 99),
        throughput_rps=len(s) / total_seconds if total_seconds > 0 else 0.0,
        errors=errors,
        error_rate=(errors / total * 100) if total > 0 else 0.0,
    )
