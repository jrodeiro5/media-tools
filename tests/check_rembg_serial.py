"""Run: python tests/check_rembg_serial.py

Background removal runs one at a time and loads its model once, even with concurrent tool calls.
A fake rembg stands in for the model, so the check needs no download.
"""

import sys
import threading
import time
import types

from PIL import Image

state = {"running": 0, "peak": 0, "sessions": 0}
guard = threading.Lock()


def new_session(_model: str) -> object:
    time.sleep(0.05)  # widen the window where two first calls could race
    with guard:
        state["sessions"] += 1
    return object()


def remove(img: Image.Image, session: object, **_kwargs: object) -> Image.Image:
    with guard:
        state["running"] += 1
        state["peak"] = max(state["peak"], state["running"])
    time.sleep(0.05)
    with guard:
        state["running"] -= 1
    return img


fake = types.ModuleType("rembg")
fake.new_session = new_session  # type: ignore[attr-defined]  # stand-in module built at runtime
fake.remove = remove  # type: ignore[attr-defined]  # stand-in module built at runtime
sys.modules["rembg"] = fake

from media_tools.tools.image import _remove_background  # noqa: E402 - needs the fake rembg first

threads = [threading.Thread(target=_remove_background, args=(Image.new("RGB", (8, 8)),)) for _ in range(6)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert state["peak"] == 1, state  # never two inferences at once
assert state["sessions"] == 1, state  # the model loads once
print("ok")
