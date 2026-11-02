"""Run a real scan against the in-process test server and write sample reports."""

from __future__ import annotations

import asyncio
import socket
import threading
import time
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import uvicorn

from sitesentry.aggregator import ScanAggregator
from sitesentry.config import ScanConfig
from sitesentry.models import ScanResult
from sitesentry.report import ReportGenerator
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


async def run_sample_scan() -> ScanResult:
    server, thread, target_url = start_server()
    try:
        cfg = ScanConfig(
            target_url=target_url,
            confirm_permission=True,
            allow_private=True,
            max_pages=5,
            rate_limit=50.0,
        )
        agg = ScanAggregator(cfg)
        result = await agg.run_scan()
        return result
    finally:
        server.should_exit = True
        thread.join(timeout=2)


def main() -> None:
    samples_dir = Path("docs/samples")
    samples_dir.mkdir(parents=True, exist_ok=True)

    print("Running sample scan against local vulnerable server...")
    result = asyncio.run(run_sample_scan())

    gen = ReportGenerator()
    json_path = samples_dir / "sample_report.json"
    md_path = samples_dir / "sample_report.md"
    html_path = samples_dir / "sample_report.html"
    sarif_path = samples_dir / "sample_report.sarif"

    json_path.write_text(gen.to_json(result), encoding="utf-8")
    md_path.write_text(gen.to_markdown(result), encoding="utf-8")
    html_path.write_text(gen.to_html(result), encoding="utf-8")
    sarif_path.write_text(gen.to_sarif(result), encoding="utf-8")

    print(f"Generated sample reports in {samples_dir}:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")
    print(f"  - {html_path}")
    print(f"  - {sarif_path}")
    print(f"Grade: {result.grade}, Score: {result.score}/100, Total Findings: {len(result.all_findings)}")


if __name__ == "__main__":
    main()
