"""Run: python tests/check_sweep.py"""

import json
import tempfile
from pathlib import Path

from media_tools.sweep import sweep
from media_tools.utils import returns_reclaim, stash_return

with tempfile.TemporaryDirectory() as d:
    src, out = Path(d) / "in", Path(d) / "out"
    src.mkdir()
    for name in ("a.png", "a.jpg"):  # both convert to a.png
        (src / name).write_bytes(b"x")
    res = json.loads(sweep(str(src), str(out), "image_convert", format="png"))
    assert any("collides" in m.get("error", "") for m in res["manifest"]), res

    orig = Path(d) / "doc.txt"
    orig.write_text("v1")
    ticket, _ = stash_return(str(orig))
    orig.write_text("v2")  # edited since the stash
    assert returns_reclaim(ticket, search_dir=str(orig.parent / "_returns")).startswith("Error"), "must not overwrite"
    assert orig.read_text() == "v2"
print("ok")
