"""Run: .venv/bin/python tests/check_probe.py"""

import json
import math
import re
import struct
import subprocess
import tempfile
import wave
import zipfile
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas

from media_tools.tools.probe import TOOLS_BY_KIND, ProbeToolkit


def probe(path: str) -> dict:
    out = ProbeToolkit.probe(path)
    assert not out.startswith("input path"), out
    assert not out.startswith("Error"), out
    res: dict = json.loads(out)
    return res


with tempfile.TemporaryDirectory() as d:
    pdf = str(Path(d) / "text.pdf")
    c = canvas.Canvas(pdf)
    c.drawString(72, 720, "Hello probe, this PDF has selectable text.")
    c.showPage()
    c.save()

    scanned = str(Path(d) / "scanned.pdf")
    c = canvas.Canvas(scanned)
    c.showPage()
    c.save()

    jpg = str(Path(d) / "photo.jpg")
    Image.new("RGB", (64, 48), (200, 30, 30)).save(jpg)

    wav = str(Path(d) / "tone.wav")
    rate, secs = 44100, 1
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        frames = b"".join(
            struct.pack("<h", int(16000 * math.sin(2 * math.pi * 440 * i / rate))) for i in range(rate * secs)
        )
        wf.writeframes(frames)

    mp4 = str(Path(d) / "clip.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=1:size=64x64:rate=10",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=1",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        mp4,
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    docx = str(Path(d) / "doc.docx")
    with zipfile.ZipFile(docx, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<w:document/>")

    txt = str(Path(d) / "note.txt")
    Path(txt).write_text("plain text, kind unknown")

    r = probe(pdf)
    assert r["kind"] == "pdf" and r["mime"] == "application/pdf", r
    assert r["pages"] == 1 and r["scanned"] is False, r
    assert r["tools"][0]["name"] == "pdf_extract_text", r["tools"][:3]

    r = probe(scanned)
    assert r["kind"] == "pdf" and r["scanned"] is True, r
    assert r["tools"][0]["name"] == "image_ocr", r["tools"][:3]

    r = probe(jpg)
    assert r["kind"] == "image" and r["mime"] == "image/jpeg", r
    assert (r["width"], r["height"]) == (64, 48) and r["has_alpha"] is False, r
    assert r["tools"][0]["name"] == "image_info", r["tools"][:3]

    r = probe(wav)
    assert r["kind"] == "audio" and abs(r["duration"] - 1.0) < 0.05 and r["has_audio"] is True, r
    assert r["tools"][0]["name"] == "audio_info", r["tools"][:3]

    r = probe(mp4)
    assert r["kind"] == "video" and r["mime"] == "video/mp4", r
    assert (r["width"], r["height"]) == (64, 64) and r["has_audio"] is True, r
    assert r["streams"] and r["tools"][0]["name"] == "video_probe", r

    r = probe(docx)
    assert r["kind"] == "office", r
    assert "office_to_markdown" in [t["name"] for t in r["tools"]], r["tools"][:3]

    r = probe(txt)
    assert r["kind"] == "unknown", r
    assert r["tools"], r

    assert ProbeToolkit.probe(str(Path(d) / "missing.pdf")).startswith("input path"), "missing must Error"

    server_names = set(re.findall(r'@mcp\.tool\(name="([^"]+)"', Path("src/media_tools/server.py").read_text()))
    ranked = {name for entries in TOOLS_BY_KIND.values() for name, _ in entries}
    assert server_names - {"media_probe"} <= ranked, server_names - {"media_probe"} - ranked
print("ok")
