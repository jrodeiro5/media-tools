# Architecture

One set of toolkits, three front doors: the MCP server, the scoped servers and the CLI. Tools never call each other over MCP; they call the toolkit classes directly.

```mermaid
flowchart LR
    client["MCP client<br/>(Claude, Cursor, OpenWebUI)"] -->|streamable-http :8020| server["server.py<br/>@mcp.tool + family tag"]
    client -.->|MEDIA_TOOLS_SEARCH=1| search["BM25SearchTransform<br/>search_tools + call_tool"] -.-> server
    shell["shell"] --> cli["cli.py<br/>argparse mirror"]
    scoped["media-tools-server-*<br/>mcp.enable(tags, only=True)"] --> server
    server --> kits
    cli --> kits
    subgraph kits["tools/ toolkits"]
        pdf["pdf.py"]
        image["image.py"]
        audio["audio.py"]
        video["video.py"]
        office["office.py"]
        pii["pii.py"]
        ai["ai.py / tts.py"]
    end
    sweep["sweep.py<br/>batch_sweep"] --> kits
    kits --> utils["utils.py<br/>validate_input / validate_output_dir<br/>stash_return / subprocess logging"]
```

## Where work actually happens

```mermaid
flowchart TB
    pdf --> pymupdf["PyMuPDF, pdfplumber,<br/>pypdfium2, reportlab, anydoc"]
    image --> pillow["Pillow, OpenCV, rembg,<br/>tesseract"]
    audio --> ffmpeg["ffmpeg / pydub"]
    video --> ffmpeg
    office --> anydoc["anydoc (to Markdown)"]
    office --> soffice["LibreOffice (to PDF)"]
    office --> officecli["officecli (inspect, edit)"]
    office -.->|url_to_markdown, cloud| firecrawl["firecrawl CLI<br/>FIRECRAWL_API_KEY"]
    pii --> presidio["Presidio recognizers<br/>(optional pii extra)"] --> pdf
    ai --> litellm["LiteLLM proxy<br/>(summarize, QA, translate, TTS, STT)"]
```

## Invariants

- Inputs go through `validate_input`, outputs through `validate_output_dir`; nothing is written in place.
- Tools return strings: a result, JSON, or `Error: ...`. They do not raise to the client.
- Only `url_to_markdown` and the LiteLLM-backed tools leave the machine; everything else is local.
- Scoped servers and `MEDIA_TOOLS_SEARCH=1` change what is listed, not what the tools do.
