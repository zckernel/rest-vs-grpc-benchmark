import asyncio
import subprocess
import sys
import os
import time
from dataclasses import dataclass

import httpx
import grpc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.rest_client import RestClient
from clients.grpc_client import GrpcClient
from benchmark.payload import generate_payload
from benchmark.metrics import compute_metrics
from monitor.resource_monitor import ResourceMonitor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class BenchmarkConfig:
    num_requests: int = 1000
    concurrency: int = 10
    warmup_requests: int = 100
    payload_size: str = "small"
    repetitions: int = 3
    rest_host: str = "127.0.0.1"
    rest_port: int = 8080
    grpc_host: str = "127.0.0.1"
    grpc_port: int = 50051


def _wait_rest(host, port, timeout=15.0):
    url = f"http://{host}:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(url, timeout=1.0).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def _wait_grpc(host, port, timeout=15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            ch = grpc.insecure_channel(f"{host}:{port}")
            grpc.channel_ready_future(ch).result(timeout=1.0)
            ch.close()
            return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


async def _load(client, payload_size, n, concurrency):
    latencies, errors = [], 0
    sem = asyncio.Semaphore(concurrency)

    async def one():
        nonlocal errors
        data = generate_payload(payload_size)
        async with sem:
            t0 = time.perf_counter()
            try:
                await client.process(payload_size, data)
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception:
                errors += 1

    await asyncio.gather(*[one() for _ in range(n)])
    return latencies, errors


async def run_rest_benchmark(cfg: BenchmarkConfig) -> dict:
    proc = subprocess.Popen(
        [sys.executable, "-m", "servers.rest_server"],
        cwd=BASE_DIR,
        env={**os.environ, "PYTHONPATH": BASE_DIR},
    )
    if not _wait_rest(cfg.rest_host, cfg.rest_port):
        proc.terminate()
        raise RuntimeError("REST server failed to start")

    monitor = ResourceMonitor(pid=proc.pid, interval=0.05)
    all_lats, all_errs = [], 0
    try:
        async with RestClient(f"http://{cfg.rest_host}:{cfg.rest_port}") as client:
            await _load(client, cfg.payload_size, cfg.warmup_requests, cfg.concurrency)
            monitor.capture_disk_before()
            monitor.start()
            t0 = time.perf_counter()
            for _ in range(cfg.repetitions):
                lats, errs = await _load(client, cfg.payload_size, cfg.num_requests, cfg.concurrency)
                all_lats.extend(lats)
                all_errs += errs
            total = time.perf_counter() - t0
            monitor.stop()
            monitor.capture_disk_after()
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    return {
        "protocol": "REST",
        "payload_size": cfg.payload_size,
        "metrics": compute_metrics(all_lats, total, all_errs),
        "resources": monitor.summary(),
        "disk_io": monitor.disk_io_delta(),
    }


async def run_grpc_benchmark(cfg: BenchmarkConfig) -> dict:
    proc = subprocess.Popen(
        [sys.executable, "-m", "servers.grpc_server"],
        cwd=BASE_DIR,
        env={**os.environ, "PYTHONPATH": BASE_DIR},
    )
    if not _wait_grpc(cfg.grpc_host, cfg.grpc_port):
        proc.terminate()
        raise RuntimeError("gRPC server failed to start")

    monitor = ResourceMonitor(pid=proc.pid, interval=0.05)
    all_lats, all_errs = [], 0
    try:
        async with GrpcClient(cfg.grpc_host, cfg.grpc_port) as client:
            await _load(client, cfg.payload_size, cfg.warmup_requests, cfg.concurrency)
            monitor.capture_disk_before()
            monitor.start()
            t0 = time.perf_counter()
            for _ in range(cfg.repetitions):
                lats, errs = await _load(client, cfg.payload_size, cfg.num_requests, cfg.concurrency)
                all_lats.extend(lats)
                all_errs += errs
            total = time.perf_counter() - t0
            monitor.stop()
            monitor.capture_disk_after()
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    return {
        "protocol": "gRPC",
        "payload_size": cfg.payload_size,
        "metrics": compute_metrics(all_lats, total, all_errs),
        "resources": monitor.summary(),
        "disk_io": monitor.disk_io_delta(),
    }
