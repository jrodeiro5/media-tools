import os
import re
import sys
import tempfile
import time


def clean_latex_artifacts(text: str) -> str:
    """
    Cleans up common LaTeX accent issues and bad character encodings in Spanish PDFs
    when processed by PDF extraction tools.
    """
    # 1. Replace composite sequences for accented characters where the accent is out of order
    # (e.g. i´o -> ió, ı´o -> ió, i´a -> iá, e´o -> eó)
    text = text.replace("ı´o", "ió").replace("i´o", "ió")
    text = text.replace("ı´a", "iá").replace("i´a", "iá")
    text = text.replace("ı´e", "ié").replace("i´e", "ié")
    text = text.replace("ı´u", "iú").replace("i´u", "iú")
    text = text.replace("e´o", "eó")

    # 2. General dotless i and standard accent replacements
    text = text.replace("´ı", "í").replace("ı´", "í")

    # 3. Standard vowels with acute accent
    text = text.replace("´a", "á").replace("a´", "á")
    text = text.replace("´e", "é").replace("e´", "é")
    text = text.replace("´i", "í").replace("i´", "í")
    text = text.replace("´o", "ó").replace("o´", "ó")
    text = text.replace("´u", "ú").replace("u´", "ú")

    text = text.replace("´A", "Á").replace("A´", "Á")
    text = text.replace("´E", "É").replace("E´", "É")
    text = text.replace("´I", "Í").replace("I´", "Í")
    text = text.replace("´O", "Ó").replace("O´", "Ó")
    text = text.replace("´U", "Ú").replace("U´", "Ú")

    # 4. Fix ñ and Ñ
    text = text.replace("n˜", "ñ").replace("N˜", "Ñ")
    text = text.replace("˜n", "ñ").replace("˜N", "Ñ")

    # 5. Split collapsed words from LaTeX spacing issues
    text = text.replace("elíndice", "el índice")
    text = text.replace("elÍndice", "el índice")

    # 6. Clean up CID characters commonly produced by pdf extraction
    text = text.replace("(cid:88)", "∑")
    text = text.replace("(cid:116)", "")
    text = text.replace("(cid:117)", "")
    text = text.replace("(cid:118)", "")
    text = text.replace("(cid:112)", "√")

    # Remove spacing accents
    text = re.sub(r"\s+´\s+", " ", text)

    return text


def run_local_markitdown(input_path: str, output_path: str):
    print("\n--- Running local MarkItDown conversion (Fast & Free) ---")
    start = time.time()
    try:
        from markitdown import MarkItDown  # type: ignore[import-not-found]

        md = MarkItDown()
        result = md.convert(input_path)
        raw_text = result.text_content

        # Clean LaTeX artifacts
        cleaned_text = clean_latex_artifacts(raw_text)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"✅ Success! Local conversion completed in {time.time() - start:.2f}s.")
        print(f"Output saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error during local conversion: {e}")


def run_mimo_ocr(input_path: str, output_path: str, api_key: str):
    print("\n--- Running MiMo Vision OCR ---")
    start = time.time()
    try:
        import base64

        import pypdfium2 as pdfium  # type: ignore[import-untyped]
        from openai import OpenAI
        from openai.types.chat.chat_completion_content_part_param import ChatCompletionContentPartParam
        from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam

        client = OpenAI(api_key=api_key, base_url="https://token-plan-ams.xiaomimimo.com/v1")

        pdf = pdfium.PdfDocument(input_path)
        total_pages = len(pdf)
        print(f"Total pages to process: {total_pages}")

        chunk_size = 5
        chunks = [list(range(i, min(i + chunk_size, total_pages))) for i in range(0, total_pages, chunk_size)]
        print(f"Processing in {len(chunks)} chunks of up to {chunk_size} pages each...")

        final_markdown: list[str] = []

        for idx, page_indices in enumerate(chunks):
            print(
                f"\nProcessing chunk {idx + 1}/{len(chunks)} (Pages {page_indices[0] + 1} to {page_indices[-1] + 1})..."
            )

            image_parts: list[ChatCompletionContentPartParam] = []
            for p in page_indices:
                page = pdf[p]
                bitmap = page.render(scale=2.0)
                pil_image = bitmap.to_pil()
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    pil_image.save(f, format="PNG")
                    tmp_path = f.name
                try:
                    with open(tmp_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    image_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
                finally:
                    os.remove(tmp_path)

            prompt = (
                f"Convert pages {page_indices[0] + 1} to {page_indices[-1] + 1} of this document into "
                "clean, well-formatted Markdown. Format tables as markdown tables, mathematical "
                "expressions as LaTeX ($...$ or $$...$$), preserve section headers. "
                "Do NOT skip or summarize any content. Output ONLY raw Markdown, no code fences."
            )
            image_parts.append({"type": "text", "text": prompt})

            messages: list[ChatCompletionUserMessageParam] = [{"role": "user", "content": image_parts}]
            response = client.chat.completions.create(
                model="mimo-v2.5",
                messages=messages,
            )
            final_markdown.append(response.choices[0].message.content or "")
            print(f"  Chunk {idx + 1} completed!")

        pdf.close()

        full_md = clean_latex_artifacts("\n\n".join(final_markdown))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_md)

        print(f"\n✅ Success! MiMo OCR completed in {time.time() - start:.2f}s.")
        print(f"Output saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error during MiMo OCR: {e}")
        print("Falling back to local MarkItDown conversion...")
        run_local_markitdown(input_path, output_path)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input.pdf> <output.md>")
        sys.exit(1)
    pdf_path, output_path = sys.argv[1], sys.argv[2]
    api_key = os.environ.get("XIAOMI_SUB_API_KEY", "")
    if api_key:
        run_mimo_ocr(pdf_path, output_path, api_key)
    else:
        run_local_markitdown(pdf_path, output_path)


if __name__ == "__main__":
    main()
