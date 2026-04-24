import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc.aio
from generated import benchmark_pb2, benchmark_pb2_grpc


class GrpcClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 50051):
        self._address = f"{host}:{port}"
        self._channel: grpc.aio.Channel | None = None
        self._stub: benchmark_pb2_grpc.BenchmarkServiceStub | None = None

    async def __aenter__(self):
        self._channel = grpc.aio.insecure_channel(self._address)
        self._stub = benchmark_pb2_grpc.BenchmarkServiceStub(self._channel)
        return self

    async def __aexit__(self, *args):
        if self._channel:
            await self._channel.close()

    async def process(self, payload_size: str, data: bytes) -> dict:
        resp = await self._stub.Process(benchmark_pb2.BenchmarkRequest(
            payload_size=payload_size,
            data=data,
            client_timestamp=int(time.time() * 1_000_000),
        ))
        return {
            "data": resp.data,
            "checksum": resp.checksum,
            "server_timestamp": resp.server_timestamp,
            "payload_size": resp.payload_size,
        }
