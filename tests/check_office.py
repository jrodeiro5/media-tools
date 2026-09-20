"""Run: python tests/check_office.py  (needs officecli)"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from media_tools.tools.office import OfficeToolkit

with tempfile.TemporaryDirectory() as d:
    src, out = str(Path(d) / "a.docx"), str(Path(d) / "b.docx")
    subprocess.run([shutil.which("officecli") or "officecli", "create", src], check=True, capture_output=True)
    cmds = json.dumps([{"command": "add", "parent": "/body", "type": "paragraph", "props": {"text": "Hola"}}])
    assert OfficeToolkit.edit(src, out, cmds).startswith("Edited"), out
    assert "Hola" in OfficeToolkit.inspect(out, "text")
    assert OfficeToolkit.edit(src, src, cmds).startswith("Error")  # never in place
    assert OfficeToolkit.edit(src, str(Path(d) / "c.docx"), '[{"command":"bogus"}]').startswith("Error")
    assert not Path(str(Path(d) / "c.docx")).exists()  # failed edit leaves no output
    assert OfficeToolkit.url_to_markdown("file:///etc/passwd").startswith("Error")
print("ok")
