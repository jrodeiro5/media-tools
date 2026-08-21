"""AI-powered document tools — summarize, QA, translate using LLM."""

from __future__ import annotations

import os
from pathlib import Path

import anydoc

from media_tools.utils import logger, validate_input, validate_output_dir


class AIToolkit:
    name = "ai"

    @staticmethod
    def _get_lite_llm_url() -> str:
        """Get LiteLLM proxy URL from environment."""
        return os.environ.get("LITELLM_URL", "http://localhost:4000")

    @staticmethod
    def _get_model() -> str:
        """Get model name from environment."""
        return os.environ.get("LLM_MODEL", "local-gemma4-e4b-vision")

    @staticmethod
    def _read_document(input_path: str) -> str:
        """Read document content using anydoc."""
        try:
            return anydoc.to_markdown(input_path)
        except Exception as exc:
            logger.error("Read document failed: %s", exc)
            return f"Error: Could not read document: {exc}"

    @staticmethod
    def _call_llm(prompt: str, document_content: str) -> str:
        """Call LLM via LiteLLM proxy."""
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url=AIToolkit._get_lite_llm_url(),
                api_key=os.environ.get("LITELLM_API_KEY", "sk-no-key-required"),
            )
            response = client.chat.completions.create(
                model=AIToolkit._get_model(),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that processes documents."},
                    {"role": "user", "content": f"{prompt}\n\nDocument content:\n{document_content}"},
                ],
                max_tokens=4096,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            return f"Error: LLM call failed: {exc}"

    @staticmethod
    def summarize(input_path: str, output: str | None = None) -> str:
        """Summarize a document using LLM (Gemma 4 e2e via LiteLLM)."""
        err = validate_input(input_path)
        if err:
            return err
        if output:
            err = validate_output_dir(output)
            if err:
                return err

        document_content = AIToolkit._read_document(input_path)
        if document_content.startswith("Error:"):
            return document_content

        summary = AIToolkit._call_llm(
            "Summarize the following document concisely. Focus on key points and main ideas.",
            document_content,
        )

        if output:
            Path(output).write_text(summary, encoding="utf-8")
            logger.info("Summarized → %s", output)
            return f"Summary → {output}"

        logger.info("Summarized document")
        return summary

    @staticmethod
    def qa(input_path: str, question: str, output: str | None = None) -> str:
        """Answer questions about a document using LLM (Gemma 4 e2e via LiteLLM)."""
        err = validate_input(input_path)
        if err:
            return err
        if output:
            err = validate_output_dir(output)
            if err:
                return err

        document_content = AIToolkit._read_document(input_path)
        if document_content.startswith("Error:"):
            return document_content

        answer = AIToolkit._call_llm(
            "Answer the following question based on the document content. "
            f"If the answer is not in the document, say so.\n\nQuestion: {question}",
            document_content,
        )

        if output:
            Path(output).write_text(answer, encoding="utf-8")
            logger.info("QA answer → %s", output)
            return f"Answer → {output}"

        logger.info("QA answered")
        return answer

    @staticmethod
    def translate(input_path: str, output: str, target_language: str = "en") -> str:
        """Translate document content using LLM (Gemma 4 e2e via LiteLLM)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        document_content = AIToolkit._read_document(input_path)
        if document_content.startswith("Error:"):
            return document_content

        translated = AIToolkit._call_llm(
            f"Translate the following document to {target_language}. Preserve formatting and structure.",
            document_content,
        )

        Path(output).write_text(translated, encoding="utf-8")
        logger.info("Translated → %s", output)
        return f"Translated to {target_language} → {output}"
