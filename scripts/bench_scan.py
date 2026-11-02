"""Benchmark scanning the local test server with varying concurrency."""

from __future__ import annotations

import asyncio
import socket
import threading
import time

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import uvicorn

from sitesentry.aggregator import ScanAggregator
from sitesentry.config import ScanConfig
from tests.fixtures.vulnerable_app import create_vulnerable_app


def start_server() -> tuple[uvicorn.Server, threading.Thread, str]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    app = create_vulnerable_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            httpx.get(url, timeout=1.0)
            break
        except Exception:
            time.sleep(0.1)
    return server, thread, url


async def run_benchmark(target_url: str, rate_limit: float) -> tuple[float, int, float]:
    cfg = ScanConfig(
        target_url=target_url,
        confirm_permission=True,
        allow_private=True,
        max_pages=20,
        rate_limit=rate_limit,
    )
    agg = ScanAggregator(cfg)
    start = time.perf_counter()
    result = await agg.run_scan()
    duration = time.perf_counter() - start

    pages_crawled = result.page_count
    # Pages plus probe requests (8 exposed file probes + 1 CORS probe)
    total_requests = pages_crawled + 9
    pages_per_sec = pages_crawled / duration if duration > 0 else 0.0

    return duration, total_requests, pages_per_sec


def main() -> None:
    server, thread, target_url = start_server()
    print(f"Server started at {target_url}\n")
    print("| Rate Limit (req/s) | Total Duration (s) | Estimated Requests | Pages / Second |")
    print("|---|---|---|---|")

    try:
        for rate in [1.0, 5.0, 20.0]:
            duration, requests_made, pps = asyncio.run(run_benchmark(target_url, rate))
            print(f"| {rate:4.1f} | {duration:6.2f}s | {requests_made:4d} | {pps:5.2f} p/s |")
    finally:
        server.should_exit = True
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
