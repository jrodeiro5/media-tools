"""Run: .venv/bin/python tests/check_tables_csv.py"""

import csv
import json
import tempfile
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Table, TableStyle

from media_tools.tools.pdf import PDFToolkit

with tempfile.TemporaryDirectory() as d:
    src = str(Path(d) / "tables.pdf")
    doc = SimpleDocTemplate(src, pagesize=A4)
    style = TableStyle([("GRID", (0, 0), (-1, -1), 0.5, "black")])
    doc.build(
        [
            Table([["name", "qty"], ["apples", "3"], ["pears", "7"]], style=style),
            PageBreak(),
            Table([["city"], ["Madrid"], ["Bilbao"]], style=style),
        ]
    )

    raw = PDFToolkit.extract_tables(src, str(Path(d) / "tables_out"))
    payload = json.loads(raw)
    assert len(payload["files"]) == 2, raw

    combined = str(Path(d) / "all.csv")
    res = PDFToolkit.tables_to_csv(src, combined)
    assert res.startswith("Tables →"), res
    with open(combined, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["page", "table", "row", "col1", "col2"], rows[0]
    per_rows = 0
    for t in payload["tables"]:
        with open(t["file"], newline="", encoding="utf-8") as f:
            per_rows += len(list(csv.reader(f)))
    assert len(rows) == 1 + per_rows, rows  # header + parity with per-table CSVs
    assert [r[0] for r in rows[1:6]] == ["1"] * 5 and [r[0] for r in rows[6:]] == ["2"] * 5, rows
    assert [r[1] for r in rows[1:]] == ["1"] * per_rows, rows
    assert any("apples" in r for r in rows), rows
    assert any("Bilbao" in r for r in rows), rows
print("ok")
