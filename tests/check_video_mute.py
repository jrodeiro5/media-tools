"""Run: .venv/bin/python tests/check_video_mute.py"""

import json
import subprocess
import tempfile
from pathlib import Path

from media_tools.tools.video import VideoToolkit

with tempfile.TemporaryDirectory() as d:
    src = str(Path(d) / "in.mp4")
    out = str(Path(d) / "muted.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=2:size=128x128:rate=30",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        src,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    res = VideoToolkit.mute(src, out)
    assert "Muted" in res, res
    probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", out]
    probe = json.loads(subprocess.run(probe_cmd, capture_output=True, text=True, check=True).stdout)
    kinds = [s.get("codec_type") for s in probe.get("streams", [])]
    assert "video" in kinds, kinds
    assert "audio" not in kinds, kinds
print("ok")
