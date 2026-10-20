"""Run: python tests/check_inference_serial.py

Heavy inferences (background removal, upscale) run one at a time, even with concurrent tool calls,
and the rembg model loads once. Fake rembg and cv2 stand in for the models, so nothing downloads.
"""

import sys
import tempfile
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


def infer() -> None:
    with guard:
        state["running"] += 1
        state["peak"] = max(state["peak"], state["running"])
    time.sleep(0.05)
    with guard:
        state["running"] -= 1


def remove(img: Image.Image, session: object, **_kwargs: object) -> Image.Image:
    infer()
    return img


class FakeSuperRes:
    def readModel(self, _path: str) -> None: ...
    def setModel(self, _name: str, _scale: int) -> None: ...
    def upsample(self, img: object) -> object:
        infer()
        return img


fake = types.ModuleType("rembg")
fake.new_session = new_session  # type: ignore[attr-defined]  # stand-in module built at runtime
fake.remove = remove  # type: ignore[attr-defined]  # stand-in module built at runtime
sys.modules["rembg"] = fake
cv2 = types.ModuleType("cv2")
cv2.dnn_superres = types.SimpleNamespace(DnnSuperResImpl=types.SimpleNamespace(create=FakeSuperRes))  # type: ignore[attr-defined]  # stand-in module built at runtime
cv2.imread = lambda _path: object()  # type: ignore[attr-defined]  # stand-in module built at runtime
cv2.imwrite = lambda _path, _img: True  # type: ignore[attr-defined]  # stand-in module built at runtime
sys.modules["cv2"] = cv2

import media_tools.tools._vision as vision  # noqa: E402 - needs the fakes first
from media_tools.tools.image import ImageToolkit, _remove_background  # noqa: E402 - needs the fakes first

vision.ensure_asset = lambda key: "model.pb"  # no download
tmp = tempfile.mkdtemp()
src = f"{tmp}/in.png"
Image.new("RGB", (8, 8)).save(src)

threads = [threading.Thread(target=_remove_background, args=(Image.new("RGB", (8, 8)),)) for _ in range(3)]
threads += [threading.Thread(target=ImageToolkit.upscale, args=(src, f"{tmp}/up{i}.png")) for i in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert state["peak"] == 1, state  # never two inferences at once
assert state["sessions"] == 1, state  # the model loads once
print("ok")
