"""Run: .venv/bin/python tests/check_faces_upscale.py (tmp fixtures + vendored face photo)"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from media_tools.tools.image import ImageToolkit
from media_tools.tools.video import VideoToolkit

FIXTURE_FACE = Path(__file__).parent / "fixtures" / "face.jpg"  # skimage astronaut, NASA public domain

with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)

    # Generated fixture: gradient PNG
    grad = tmp / "grad.png"
    img = Image.new("RGB", (64, 64))
    px = img.load()
    assert px is not None
    for x in range(64):
        for y in range(64):
            px[x, y] = (x * 4, y * 4, (x + y) * 2)
    img.save(grad)

    # image_upscale x2/x3 (FSRCNN, download-on-first-run)
    up2 = tmp / "up2.png"
    assert ImageToolkit.upscale(str(grad), str(up2), 2).startswith("Upscaled x2"), up2
    w, h = Image.open(up2).size
    assert (w, h) == (128, 128), (w, h)
    up3 = tmp / "up3.png"
    assert ImageToolkit.upscale(str(grad), str(up3), 3).startswith("Upscaled x3"), up3
    w, h = Image.open(up3).size
    assert (w, h) == (192, 192), (w, h)
    assert ImageToolkit.upscale(str(grad), str(tmp / "bad.png"), 4).startswith("Error: scale"), "scale gate"

    # faces:0 is success — blank image still yields a written output
    blank = tmp / "blank.png"
    Image.new("RGB", (200, 200), (10, 20, 30)).save(blank)
    blank_out = tmp / "blank_out.png"
    res = ImageToolkit.blur_faces(str(blank), str(blank_out))
    assert res.startswith("Blurred 0 faces"), res
    assert blank_out.is_file()
    assert ImageToolkit.blur_faces(str(blank), str(tmp / "m.png"), "smear").startswith("Error: mode"), "mode gate"

    # Vendored face photo — canonical frontal face, Haar must find >= 1
    face = tmp / "face.jpg"
    shutil.copy(FIXTURE_FACE, face)
    face_out = tmp / "face_out.png"
    res = ImageToolkit.blur_faces(str(face), str(face_out))
    assert res.startswith("Blurred ") and "faces (pixelate)" in res, res
    n = int(res.split(" ")[1])
    assert n >= 1, res
    assert face_out.read_bytes() != face.read_bytes(), "face region must change"
    face_blur = tmp / "face_blur.png"
    assert ImageToolkit.blur_faces(str(face), str(face_blur), "blur").startswith("Blurred "), "blur mode"

    # Generated fixture: 2s testsrc clip -> video_blur_faces (faces:0 success, JSON payload)
    clip = tmp / "clip.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=160x120:rate=10:duration=2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(clip),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]
    vout = tmp / "clip_blur.mp4"
    payload = json.loads(VideoToolkit.blur_faces(str(clip), str(vout), every_n_frames=5))
    assert payload["frames_processed"] == 20, payload
    assert payload["frames_with_faces"] == 0 and payload["max_faces"] == 0, payload
    assert vout.is_file()
    assert VideoToolkit.blur_faces(str(clip), str(tmp / "e.mp4"), 0).startswith("Error:"), "n_frames gate"
print("ok")
