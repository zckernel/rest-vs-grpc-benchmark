# REST/JSON vs gRPC/Protobuf Benchmark

Compares protocol + serialization overhead between FastAPI/REST and gRPC/Protobuf under identical conditions.

## Quick start

```bash
cd app/api_performance
pip install -r requirements.txt
python run_benchmark.py
```

## Options

| Flag             | Default    | Description                              |
|------------------|------------|------------------------------------------|
| `--payload-size` | small      | small (100 B), medium (10 KB), large (1 MB) |
| `--requests`     | 1000       | Requests per repetition                  |
| `--concurrency`  | 10         | Concurrent async workers                 |
| `--warmup`       | 100        | Warmup requests (excluded from results)  |
| `--repetitions`  | 3          | Repetitions (results aggregated)         |
| `--output-dir`   | results/   | Directory for JSON + CSV output          |
| `--protocols`    | rest,grpc  | Run one or both                          |

## Run tests

```bash
# Unit tests only (fast, no servers needed)
python -m pytest tests/ --ignore=tests/test_equivalence.py -v

# Equivalence test (starts real servers on ports 8080 / 50051)
python -m pytest tests/test_equivalence.py -v
```

## Regenerate proto stubs

```bash
python -m grpc_tools.protoc -I proto --python_out=generated --grpc_python_out=generated proto/benchmark.proto
# Fix import in generated file:
sed -i 's/^import benchmark_pb2/from generated import benchmark_pb2/' generated/benchmark_pb2_grpc.py
```

## Architecture

```
run_benchmark.py
  ├── run_rest_benchmark()  → subprocess: servers/rest_server.py (port 8080)
  │     └── FastAPI /process → core/logic.process_payload()
  ├── run_grpc_benchmark()  → subprocess: servers/grpc_server.py (port 50051)
  │     └── BenchmarkServicer.Process() → core/logic.process_payload()
  ├── Warmup phase (excluded from metrics)
  ├── Async load: httpx / grpc.aio, semaphore-limited concurrency
  ├── ResourceMonitor: psutil polling every 200 ms
  └── reporter: table + JSON + CSV
```

## Business logic (identical for both)

`core/logic.process_payload(size, data)`:
1. SHA-256 checksum of raw bytes
2. Returns: data (echo), checksum, server_timestamp (µs), payload_size

## Assumptions

- REST uses HTTP/1.1; gRPC uses HTTP/2. Intentional — reflects real deployment.
- REST binary data is base64-encoded in JSON; gRPC uses native bytes. Encoding cost is measured.
- Both servers run as local subprocesses on loopback.

## Limitations

- CPU/RAM metrics require ≥1000 requests to accumulate meaningful psutil samples.
- `psutil.cpu_percent()` first call always returns 0.0 (psutil design).
- Disk I/O is system-wide delta, not per-process.
- Single-worker servers (uvicorn, asyncio gRPC). Use `--workers` flags for multi-core testing.
- Loopback eliminates network as a variable — results will differ on real networks.

## Interpreting results

- **Lower latency + higher throughput** = more efficient protocol for that payload.
- gRPC typically wins: smaller wire format, no base64, HTTP/2 multiplexing.
- REST/JSON may be competitive for large payloads where relative encoding overhead is smaller.
- CPU difference reflects serialization cost (JSON encode/decode vs protobuf).
