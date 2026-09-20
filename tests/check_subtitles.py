"""Run: .venv/bin/python tests/check_subtitles.py"""

import json
import os
import re
import socket
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

from media_tools.tools.audio import AudioToolkit
from media_tools.tools.video import VideoToolkit

STAMP = re.compile(r"^(\d{2,}:\d{2}:\d{2},\d{3}) --> (\d{2,}:\d{2}:\d{2},\d{3})$")


def _to_ms(stamp: str) -> int:
    h, m, rest = stamp.split(":")
    s, ms = rest.split(",")
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def _validate_srt(text: str, expect_cues: int) -> None:
    blocks = [b for b in text.strip().split("\n\n") if b.strip()]
    assert len(blocks) == expect_cues, f"want {expect_cues} cues, got {len(blocks)}:\n{text}"
    prev_start = -1
    for i, block in enumerate(blocks, 1):
        lines = block.split("\n")
        assert lines[0] == str(i), f"cue {i} misnumbered: {lines[0]!r}"
        m = STAMP.match(lines[1])
        assert m, f"cue {i} bad timestamp: {lines[1]!r}"
        start, end = m.groups()
        assert _to_ms(start) < _to_ms(end), f"cue {i} start >= end"
        assert _to_ms(start) >= prev_start, f"cue {i} not monotonic"
        prev_start = _to_ms(start)
        assert any(line.strip() for line in lines[2:]), f"cue {i} has no text"


def _proxy_reachable() -> bool:
    url = os.environ.get("LITELLM_URL", "http://localhost:4000")
    parts = urllib.parse.urlparse(url)
    host = parts.hostname or "localhost"
    port = parts.port or 4000
    try:
        socket.create_connection((host, port), timeout=2).close()
        return True
    except OSError:
        return False


with tempfile.TemporaryDirectory() as d:
    tjson = str(Path(d) / "transcript.json")
    segments = [
        {"index": 0, "start_ms": 500, "start_s": 0.5, "duration_ms": 1500, "text": "hello world"},
        {"index": 1, "start_ms": 2500, "start_s": 2.5, "duration_ms": 2000, "text": "   "},
        {"index": 2, "start_ms": 5000, "start_s": 5.0, "duration_ms": 1250, "text": "second cue"},
        {"index": 3, "start_ms": 3723000, "start_s": 3723.0, "duration_ms": 250, "text": "hour mark"},
    ]
    Path(tjson).write_text(json.dumps({"segments": segments, "text": "hello world\nsecond cue\nhour mark"}))

    # path input
    srt1 = str(Path(d) / "a.srt")
    raw = AudioToolkit.transcript_to_srt(tjson, srt1)
    info = json.loads(raw)
    assert info["cues"] == 3, raw  # empty text skipped
    body = Path(srt1).read_text()
    _validate_srt(body, 3)
    assert "1\n00:00:00,500 --> 00:00:02,000\nhello world\n" in body, body
    assert "3\n01:02:03,000 --> 01:02:03,250\nhour mark\n" in body, body

    # raw segments JSON string input (bare list)
    srt2 = str(Path(d) / "b.srt")
    raw2 = AudioToolkit.transcript_to_srt(json.dumps(segments[:1]), srt2)
    assert json.loads(raw2)["cues"] == 1, raw2
    _validate_srt(Path(srt2).read_text(), 1)

    # error paths
    assert AudioToolkit.transcript_to_srt("not json {{", srt2).startswith("Error:"), "bad json must fail"
    empty = str(Path(d) / "empty.json")
    Path(empty).write_text(json.dumps({"segments": []}))
    assert AudioToolkit.transcript_to_srt(empty, srt2).startswith("Error:"), "empty segments must fail"

    # real clip + burn round-trip
    clip = str(Path(d) / "in.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=4:size=128x128:rate=30",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=4",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        clip,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    probe_cmd = ["ffmpeg", "-hide_banner", "-h", "filter=subtitles"]
    libass = subprocess.run(probe_cmd, capture_output=True, text=True)
    has_libass = libass.returncode == 0 and "Unknown filter" not in (libass.stdout + libass.stderr)
    if has_libass:
        burned = str(Path(d) / "burned.mp4")
        res = VideoToolkit.subtitle_burn(clip, srt1, burned)
        assert "Burned" in res, res
        assert Path(burned).is_file() and Path(burned).stat().st_size > 0, res
        print("burn: ok")
    else:
        print("burn: SKIPPED (ffmpeg lacks libass)")

    if _proxy_reachable():
        out_dir = str(Path(d) / "transcript")
        res = VideoToolkit.transcribe(clip, out_dir)
        try:
            data = json.loads(res)
        except json.JSONDecodeError:
            data = None
        # sine tone carries no speech: chain success means the 3 keys,
        # honest empty-transcript means the recipe ran end-to-end anyway
        assert (isinstance(data, dict) and {"srt", "transcript_json", "txt"} <= set(data)) or res.startswith(
            "Error: all segments have empty text"
        ), res
        print(f"video_transcribe: ok (live proxy: {res[:120]})")
    else:
        print("video_transcribe: SKIPPED (LiteLLM proxy unreachable at localhost:4000)")
print("ok")
