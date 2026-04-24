import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import grpc.aio
from generated import benchmark_pb2, benchmark_pb2_grpc
from core.logic import process_payload

_PORT = 50051


class BenchmarkServicer(benchmark_pb2_grpc.BenchmarkServiceServicer):
    async def Process(self, request, context):
        result = process_payload(request.payload_size, request.data)
        return benchmark_pb2.BenchmarkResponse(
            data=result["data"],
            checksum=result["checksum"],
            server_timestamp=result["server_timestamp"],
            payload_size=result["payload_size"],
        )


async def serve():
    server = grpc.aio.server()
    benchmark_pb2_grpc.add_BenchmarkServiceServicer_to_server(BenchmarkServicer(), server)
    server.add_insecure_port(f"[::]:{_PORT}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
