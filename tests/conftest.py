"""Shared pytest fixtures."""

from __future__ import annotations

import threading
from collections.abc import Generator

import pytest
import uvicorn


@pytest.fixture(scope="session")
def vulnerable_server_url() -> Generator[str, None, None]:
    """Start the vulnerable test server on an ephemeral port, yield URL, shut down."""
    import socket

    from tests.fixtures.vulnerable_app import create_vulnerable_app

    # Find a free port
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    app = create_vulnerable_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for startup
    import time

    for _ in range(50):
        try:
            import httpx

            httpx.get(f"http://127.0.0.1:{port}/", timeout=1.0)
            break
        except Exception:
            time.sleep(0.1)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)
