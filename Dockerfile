FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    HOST=0.0.0.0 \
    PORT=8020

# ffmpeg (audio/video + libass for subtitle burn), tesseract (OCR),
# ghostscript (pdf_to_a), libreoffice (office/pdf/docx conversion), fonts.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    ghostscript \
    libreoffice \
    fonts-dejavu \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev --no-editable \
 && useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app

EXPOSE 8020
USER appuser
CMD ["/app/.venv/bin/media-tools-server"]
