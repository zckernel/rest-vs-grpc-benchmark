import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from generated import benchmark_pb2
from servers.grpc_server import BenchmarkServicer


@pytest.fixture
def servicer():
    return BenchmarkServicer()


@pytest.mark.asyncio
async def test_checksum(servicer):
    data = b"hello grpc"
    req = benchmark_pb2.BenchmarkRequest(payload_size="small", data=data, client_timestamp=0)
    resp = await servicer.Process(req, context=None)
    assert resp.checksum == hashlib.sha256(data).hexdigest()


@pytest.mark.asyncio
async def test_echoes_data(servicer):
    data = b"echo"
    req = benchmark_pb2.BenchmarkRequest(payload_size="medium", data=data, client_timestamp=0)
    resp = await servicer.Process(req, context=None)
    assert resp.data == data


@pytest.mark.asyncio
async def test_payload_size_field(servicer):
    req = benchmark_pb2.BenchmarkRequest(payload_size="large", data=b"x", client_timestamp=0)
    resp = await servicer.Process(req, context=None)
    assert resp.payload_size == "large"


@pytest.mark.asyncio
async def test_timestamp_positive(servicer):
    req = benchmark_pb2.BenchmarkRequest(payload_size="small", data=b"t", client_timestamp=0)
    resp = await servicer.Process(req, context=None)
    assert resp.server_timestamp > 0
