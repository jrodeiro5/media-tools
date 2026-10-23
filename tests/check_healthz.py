"""Run: .venv/bin/python tests/check_healthz.py"""

from starlette.testclient import TestClient

from media_tools.server import mcp

with TestClient(mcp.http_app(transport="streamable-http", stateless_http=True)) as client:
    r = client.get("/healthz")
    assert (r.status_code, r.text) == (200, "ok"), (r.status_code, r.text)
print("ok")
