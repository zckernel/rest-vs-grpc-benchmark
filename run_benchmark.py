#!/usr/bin/env python3
import argparse
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark.runner import BenchmarkConfig, run_rest_benchmark, run_grpc_benchmark
from benchmark.reporter import print_table, save_json, save_csv, build_table_rows


def parse_args():
    p = argparse.ArgumentParser(description="REST vs gRPC benchmark")
    p.add_argument("--payload-size", default="small", choices=["small", "medium", "large"])
    p.add_argument("--requests",     type=int, default=1000)
    p.add_argument("--concurrency",  type=int, default=10)
    p.add_argument("--warmup",       type=int, default=100)
    p.add_argument("--repetitions",  type=int, default=3)
    p.add_argument("--output-dir",   default="results")
    p.add_argument("--protocols",    default="rest,grpc")
    return p.parse_args()


async def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    protocols = [p.strip().lower() for p in args.protocols.split(",")]

    cfg = BenchmarkConfig(
        num_requests=args.requests,
        concurrency=args.concurrency,
        warmup_requests=args.warmup,
        payload_size=args.payload_size,
        repetitions=args.repetitions,
    )

    results = {}

    if "rest" in protocols:
        print(f"[REST] payload={args.payload_size}, requests={args.requests}×{args.repetitions}, concurrency={args.concurrency}")
        results["rest"] = await run_rest_benchmark(cfg)
        print("[REST] done.")

    if "grpc" in protocols:
        print(f"[gRPC] payload={args.payload_size}, requests={args.requests}×{args.repetitions}, concurrency={args.concurrency}")
        results["grpc"] = await run_grpc_benchmark(cfg)
        print("[gRPC] done.")

    if "rest" in results and "grpc" in results:
        print_table(results["rest"], results["grpc"], args.payload_size)
        ts = int(time.time())
        json_path = os.path.join(args.output_dir, f"results_{args.payload_size}_{ts}.json")
        csv_path  = os.path.join(args.output_dir, f"results_{args.payload_size}_{ts}.csv")
        save_json(json_path, [results["rest"], results["grpc"]])
        save_csv(csv_path, build_table_rows(results["rest"], results["grpc"]))
        print(f"\nSaved: {json_path}\n       {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())
