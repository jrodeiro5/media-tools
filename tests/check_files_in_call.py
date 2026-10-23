"""Run: .venv/bin/python tests/check_files_in_call.py"""

import asyncio
import base64
import io
import os
import tempfile
from pathlib import Path

root = Path(tempfile.mkdtemp())
os.environ["MEDIA_TOOLS_ROOT"] = str(root)
os.environ["MEDIA_TOOLS_FILES_IN_CALL"] = "1"

from fastmcp import Client  # noqa: E402
from PIL import Image  # noqa: E402

from media_tools.server import mcp  # noqa: E402

buf = io.BytesIO()
Image.new("RGB", (8, 8), "red").save(buf, "PNG")
png = base64.b64encode(buf.getvalue()).decode()


async def main() -> None:
    async with Client(mcp) as c:
        args = {
            "tool": "image_grayscale",
            "args": {},
            # A name that tries to leave the work folder lands inside it.
            "files": {"input_path": {"name": "../../photo.png", "b64": png}},
            "outputs": {"output": "gray.png"},
        }
        got = (await c.call_tool("call_with_files", args)).structured_content
        assert got["result"].startswith("Grayscale"), got["result"]
        assert Image.open(io.BytesIO(base64.b64decode(got["files"]["gray.png"]))).mode == "L"
        try:
            await c.call_tool("call_with_files", {**args, "tool": "call_with_files"})
            raise AssertionError("called itself")
        except Exception as exc:  # noqa: BLE001
            assert "cannot call itself" in str(exc), exc
    assert list(root.iterdir()) == [], "the work folder is removed"


asyncio.run(main())
print("ok")
