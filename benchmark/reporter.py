import csv
import json
import dataclasses
from tabulate import tabulate
from benchmark.metrics import MetricsResult


def build_table_rows(rest: dict, grpc: dict) -> list[tuple]:
    rm, gm = rest["metrics"], grpc["metrics"]
    rr, gr = rest["resources"], grpc["resources"]
    rd, gd = rest.get("disk_io", {}), grpc.get("disk_io", {})

    def f(v, d=2):
        return f"{v:.{d}f}" if isinstance(v, float) else str(v)

    return [
        ("Avg Latency (ms)",   f(rm.avg_ms),             f(gm.avg_ms)),
        ("p50 (ms)",           f(rm.p50_ms),             f(gm.p50_ms)),
        ("p95 (ms)",           f(rm.p95_ms),             f(gm.p95_ms)),
        ("p99 (ms)",           f(rm.p99_ms),             f(gm.p99_ms)),
        ("Throughput (req/s)", f(rm.throughput_rps, 1),  f(gm.throughput_rps, 1)),
        ("Errors",             str(rm.errors),            str(gm.errors)),
        ("Error Rate (%)",     f(rm.error_rate),          f(gm.error_rate)),
        ("Avg CPU %",          f(rr["avg_cpu_percent"]),  f(gr["avg_cpu_percent"])),
        ("Max CPU %",          f(rr["max_cpu_percent"]),  f(gr["max_cpu_percent"])),
        ("Avg RAM (MB)",       f(rr["avg_rss_mb"]),       f(gr["avg_rss_mb"])),
        ("Max RAM (MB)",       f(rr["max_rss_mb"]),       f(gr["max_rss_mb"])),
        ("Disk Read (B)",      str(rd.get("read_bytes", 0)),  str(gd.get("read_bytes", 0))),
        ("Disk Write (B)",     str(rd.get("write_bytes", 0)), str(gd.get("write_bytes", 0))),
    ]


def print_table(rest: dict, grpc: dict, payload_size: str):
    rows = build_table_rows(rest, grpc)
    print(f"\n{'='*58}")
    print(f" Benchmark Results — payload_size={payload_size}")
    print('='*58)
    print(tabulate(rows, headers=["Metric", "REST/JSON", "gRPC/Protobuf"], tablefmt="grid"))


def save_json(path: str, results: list[dict]):
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=lambda o: dataclasses.asdict(o) if dataclasses.is_dataclass(o) else str(o))


def save_csv(path: str, rows: list[tuple]):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Metric", "REST", "gRPC"])
        w.writerows(rows)
