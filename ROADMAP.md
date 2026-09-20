# Roadmap — media_tools, la navaja suiza multimedia

Fuente técnica: `BACKLOG.md`. Orden: quick win → complejo (escalera ponytail: sin dependencias nuevas primero).

## Shipped

- Lote 1 paridad (2026-09-20): `video_mute`, `html_to_pdf`, `pdf_tables_to_csv`, `image_grayscale/sharpen/circle_crop/split_tiles` — 90→97 tools.
- Fixes: `pdf_fill_form` (/AcroForm), `remove_background` (SystemExit→Error), `returns_reclaim.search_dir`, `openai` obligatoria + `ImportError` amable, pre-check libass en `subtitle_burn`.

## Next — sin dependencias nuevas

1. `media_probe` — un JSON por fichero + ranking de tools aplicables (solo backends ya exigidos).
2. OCR-skip — `extract_text_smart`: tesseract solo en páginas sin text-layer.
3. Refusal tickets — `{code, reason, fix_hint, remedy}` string-compatible con `Error:`.
4. Check paridad `salvage` vs Repair-PDF de iLove (cerrar o abrir `pdf_repair`).
5. Higiene docs: `ghostscript`/libass/onnxruntime a Requirements, `.mcp.json` a 2 entradas.

## Then — con decisión de dependencia

6. `image_upscale` — falta elegir modelo (candidatos: Real-ESRGAN ligero vs remini-cloud, no local).
7. `pdf_to_pptx` — spike previo: ¿`soffice --convert-to pptx` desde PDF/Draw da fidelidad aceptable? Si no, pymupdf+python-pptx manual.
8. `pdf_to_xlsx` — idem vía extracción de tablas existente + openpyxl (ya indirecto).
9. `transcribe` local (whisper) — hoy solo vía proxy LiteLLM.

## Later — apuestas ADHD

- `video_ocr_to_srt` (ffmpeg+tesseract), recipes de multi-paso, `probe --plan`, sweep con dedupe por hash.

## No hacemos

Watermark-removal (abuso), descargadores sociales (ToS), WYSIWYG/firma/scan hospedados, escritura IA (fuera de scope: ficheros multimedia).
