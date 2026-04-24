import asyncio
import hashlib
import subprocess
import sys
import os
import time

import httpx
import grpc
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.rest_client import RestClient
from clients.grpc_client import GrpcClient
from benchmark.payload import generate_payload

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


@pytest.fixture(scope="module")
def rest_proc():
    p = subprocess.Popen(
        [sys.executable, "-m", "servers.rest_server"],
        cwd=BASE_DIR,
        env={**os.environ, "PYTHONPATH": BASE_DIR},
    )
    assert _wait_rest("127.0.0.1", 8080), "REST server did not start"
    yield p
    p.terminate(); p.wait(timeout=5)


@pytest.fixture(scope="module")
def grpc_proc():
    p = subprocess.Popen(
        [sys.executable, "-m", "servers.grpc_server"],
        cwd=BASE_DIR,
        env={**os.environ, "PYTHONPATH": BASE_DIR},
    )
    assert _wait_grpc("127.0.0.1", 50051), "gRPC server did not start"
    yield p
    p.terminate(); p.wait(timeout=5)


@pytest.mark.asyncio
@pytest.mark.parametrize("size", ["small", "medium"])
async def test_checksums_match(rest_proc, grpc_proc, size):
    data = generate_payload(size)
    expected = hashlib.sha256(data).hexdigest()

    async with RestClient("http://127.0.0.1:8080") as rc:
        rest = await rc.process(size, data)

    async with GrpcClient("127.0.0.1", 50051) as gc:
        grpc_ = await gc.process(size, data)

    assert rest["checksum"] == expected, "REST checksum mismatch"
    assert grpc_["checksum"] == expected, "gRPC checksum mismatch"
    assert rest["checksum"] == grpc_["checksum"]
    assert rest["data"] == data
    assert grpc_["data"] == data
