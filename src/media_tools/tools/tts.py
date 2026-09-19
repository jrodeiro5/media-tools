"""Text-to-Speech toolkit using the local LiteLLM proxy (omlx / Kokoro)."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from media_tools.utils import logger, validate_output_dir

# Kokoro emits 24 kHz mono int16.
_SAMPLE_RATE = 24000
_BYTES_PER_SAMPLE = 2

# Default voice per language. Kokoro voice ids encode language+gender:
# a=en-US, b=en-GB, e=es, f=fr, h=hi, i=it, j=ja, p=pt-BR, z=zh.
# Full list in VOICES.md inside the model snapshot.
_DEFAULT_VOICES = {
    "en": "af_heart",
    "es": "ef_dora",
    "fr": "ff_siwis",
    "it": "if_sara",
    "pt": "pf_dora",
    "ja": "jf_alpha",
    "zh": "zf_xiaobei",
    "hi": "hf_alpha",
}


class TTSToolkit:
    name = "tts"

    @staticmethod
    def _endpoint() -> str:
        base = os.environ.get("LITELLM_URL", "http://localhost:4000").rstrip("/")
        return f"{base}/v1/audio/speech"

    @staticmethod
    def _model() -> str:
        return os.environ.get("TTS_MODEL", "local-kokoro-tts")

    @staticmethod
    def convert(
        text: str,
        output: str,
        voice: str = "",
        audio_format: str = "wav",
        language: str = "en",
        timeout: int = 300,
    ) -> str:
        """Convert text to speech locally. No API key, no network egress.

        Args:
            text: Text to convert to speech
            output: Output audio file path
            voice: Kokoro voice id (e.g. "af_heart", "ef_dora"). Empty picks
                the default voice for `language`.
            audio_format: "wav" (native) or "mp3" (converted via pydub/ffmpeg)
            language: ISO code used to pick the default voice and G2P
            timeout: Seconds to wait for generation
        """
        err = validate_output_dir(output)
        if err:
            return err
        if not text.strip():
            return "Error: text is empty"

        voice = voice or _DEFAULT_VOICES.get(language, "af_heart")

        payload = json.dumps(
            {
                "model": TTSToolkit._model(),
                "input": text,
                "voice": voice,
                "response_format": "wav",
                "language": language,
            }
        ).encode()
        req = urllib.request.Request(
            TTSToolkit._endpoint(),
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('LITELLM_API_KEY', 'sk-no-key-required')}",
            },
        )

        # endpoint is TTSToolkit._endpoint(), built from LITELLM_URL env var,
        # not from any tool argument (text/voice/language) — not attacker-controlled.
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
                audio = resp.read()
        except Exception as exc:
            logger.error("TTS failed: %s", exc)
            return f"Error: {exc}"

        seconds = max(len(audio) - 44, 0) / (_SAMPLE_RATE * _BYTES_PER_SAMPLE)

        if audio_format == "mp3":
            try:
                import io

                from pydub import AudioSegment

                AudioSegment.from_wav(io.BytesIO(audio)).export(output, format="mp3")
            except Exception as exc:
                logger.error("mp3 export failed: %s", exc)
                return f"Error: mp3 export failed ({exc}). Use audio_format='wav'."
        else:
            Path(output).write_bytes(audio)

        logger.info("TTS converted → %s", output)
        return f"Speech → {output} ({audio_format.upper()}, {seconds:.1f}s, voice={voice})"
