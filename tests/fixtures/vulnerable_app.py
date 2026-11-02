"""Local misconfigured test server for integration tests.

Deliberately serves security-problematic responses to test SiteSentry checks.
Runs in-process on an ephemeral port.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse


def create_vulnerable_app() -> FastAPI:
    """Create the deliberately misconfigured FastAPI test app."""
    app = FastAPI()

    @app.middleware("http")
    async def add_bad_headers(request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[operator]
        # Deliberately missing security headers
        # (No CSP, No HSTS, No X-Frame-Options, No X-Content-Type-Options,
        #  No Referrer-Policy, No Permissions-Policy)
        # Add tech disclosure headers
        response.headers["Server"] = "Apache/2.4.49"
        response.headers["X-Powered-By"] = "PHP/7.4.3"
        return response

    @app.get("/")
    async def root() -> HTMLResponse:
        html = """<!DOCTYPE html>
<html>
<head><title>Vulnerable Test App</title></head>
<body>
<h1>Test App</h1>
<!-- Mixed content: HTTP resource on a page served over HTTP (for test) -->
<script src="http://cdn.example.com/jquery.min.js"></script>
<!-- External script without SRI -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/js/bootstrap.bundle.min.js"></script>
<!-- External stylesheet without SRI -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css">
<a href="/page2">Page 2</a>
<a href="/secret-dir/">Secret Dir</a>
</body>
</html>"""
        resp = HTMLResponse(html)
        # Set insecure cookie
        resp.set_cookie(
            "session_id",
            "abc123",
            # deliberately missing Secure, HttpOnly, SameSite
        )
        return resp

    @app.get("/page2")
    async def page2() -> HTMLResponse:
        html = """<!DOCTYPE html>
<html>
<head><title>Page 2</title></head>
<body><h1>Page 2</h1><a href="/">Home</a></body>
</html>"""
        return HTMLResponse(html)

    @app.get("/secret-dir/")
    async def directory_listing() -> HTMLResponse:
        html = """<!DOCTYPE html>
<html>
<head><title>Index of /secret-dir/</title></head>
<body>
<h1>Index of /secret-dir/</h1>
<ul>
<li><a href="secret.txt">secret.txt</a></li>
<li><a href="passwords.txt">passwords.txt</a></li>
</ul>
</body>
</html>"""
        return HTMLResponse(html)

    @app.get("/.git/HEAD")
    async def git_head() -> PlainTextResponse:
        # A real .git/HEAD starts with "ref:"
        return PlainTextResponse("ref: refs/heads/main\n")

    @app.get("/.env")
    async def env_file() -> PlainTextResponse:
        # Returns a fake .env – tests should NOT read or store the content
        return PlainTextResponse("DB_PASSWORD=secret\nSECRET_KEY=abc123\n")

    @app.get("/.DS_Store")
    async def ds_store() -> Response:
        return Response(content=b"\x00\x00\x00\x01Bud1", media_type="application/octet-stream")

    @app.get("/robots.txt")
    async def robots() -> PlainTextResponse:
        return PlainTextResponse("User-agent: *\nDisallow: /admin/\n")

    @app.get("/cors-endpoint")
    async def cors_endpoint(request: Request) -> Response:
        # Reflects any Origin header – CORS misconfiguration
        origin = request.headers.get("origin", "")
        resp = Response(content='{"data": "test"}', media_type="application/json")
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp

    # Soft-404: any unknown path returns 200 with custom body
    @app.api_route("/{path:path}", methods=["GET", "HEAD"])
    async def catch_all(path: str) -> HTMLResponse:
        return HTMLResponse(
            f"<html><body><h1>Custom 404 - Not Found</h1><p>/{path}</p></body></html>",
            status_code=200,
        )

    return app


# Standalone runner for manual testing
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_vulnerable_app(), host="127.0.0.1", port=8765)
