"""Run: MEDIA_TOOLS_ROOT=/tmp/mt-root .venv/bin/python tests/check_limits.py (in the media-tools image)."""

import asyncio
import os
import tempfile
import time
from pathlib import Path

root = Path(os.environ["MEDIA_TOOLS_ROOT"])
root.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MEDIA_TOOLS_MAX_BYTES", "1000")

from PIL import Image  # noqa: E402

from media_tools import utils  # noqa: E402
from media_tools.tools.image import ImageToolkit  # noqa: E402

inside = root / "a.png"
Image.new("RGB", (8, 8)).save(inside)
with tempfile.TemporaryDirectory() as d:
    outside = Path(d) / "b.png"
    Image.new("RGB", (8, 8)).save(outside)
    assert "outside" in ImageToolkit.grayscale(str(outside), str(root / "o.png")), "input outside root"
    assert "outside" in ImageToolkit.grayscale(str(inside), str(Path(d) / "o.png")), "output outside root"
    link = root / "link.png"
    link.symlink_to(outside)
    assert "outside" in ImageToolkit.grayscale(str(link), str(root / "o.png")), "symlink out of root"
assert "URLs are disabled" in (utils.validate_input("http://169.254.169.254/x") or ""), "SSRF"
assert ImageToolkit.grayscale(str(inside), str(root / "o.png")).startswith("Grayscale"), "inside works"
big = root / "big.png"
Image.effect_noise((64, 64), 50).save(big)
assert "over 1000 bytes" in ImageToolkit.grayscale(str(big), str(root / "o.png")), "size cap"

from fastmcp import Client, FastMCP  # noqa: E402

from media_tools.server import Limits  # noqa: E402

srv = FastMCP("t")
srv.add_middleware(Limits(1, 0.5))


@srv.tool
def slow(seconds: float) -> str:
    time.sleep(seconds)
    return "done"


async def main() -> None:
    async with Client(srv) as c:
        assert (await c.call_tool("slow", {"seconds": 0.1})).data == "done"
        try:
            await c.call_tool("slow", {"seconds": 2})
            raise AssertionError("no timeout")
        except Exception as exc:  # noqa: BLE001
            assert "took longer" in str(exc), exc


asyncio.run(main())
print("ok")
