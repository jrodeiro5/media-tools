"""Text-to-Speech toolkit using Fish Audio SDK."""

from __future__ import annotations

import os
from pathlib import Path

from media_tools.utils import logger, validate_input, validate_output_dir


class TTSToolkit:
    name = "tts"

    @staticmethod
    def convert(
        text: str,
        output: str,
        voice_id: str | None = None,
        speed: float = 1.0,
        audio_format: str = "mp3",
        latency: str = "balanced",
        reference_audio: str | None = None,
        reference_text: str | None = None,
    ) -> str:
        """Convert text to speech using Fish Audio.

        Args:
            text: Text to convert to speech
            output: Output audio file path
            voice_id: Pre-defined voice ID (optional)
            speed: Speech speed (0.5-2.0, default 1.0)
            audio_format: Output format (mp3, wav, pcm, opus)
            latency: Latency mode (normal, balanced)
            reference_audio: Path to reference audio for voice cloning
            reference_text: Text spoken in reference audio (for cloning)
        """
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from fishaudio import FishAudio
            from fishaudio.types import ReferenceAudio, TTSConfig, Prosody

            api_key = os.environ.get("FISH_API_KEY")
            if not api_key:
                return "Error: FISH_API_KEY not set. Get one at https://fish.audio"

            client = FishAudio(api_key=api_key)

            # Build references for voice cloning if provided
            references = None
            if reference_audio:
                err_ref = validate_input(reference_audio)
                if err_ref:
                    return err_ref
                if not reference_text:
                    return "Error: reference_text required when using reference_audio"

                with open(reference_audio, "rb") as f:
                    audio_bytes = f.read()
                references = [
                    ReferenceAudio(audio=audio_bytes, text=reference_text)
                ]

            # Build config
            config = TTSConfig(
                reference_id=voice_id,
                format=audio_format,
                latency=latency,
                prosody=Prosody(speed=speed),
            )

            # Convert
            audio = client.tts.convert(
                text=text,
                config=config,
                references=references,
            )

            # Save to file
            Path(output).write_bytes(audio)
            logger.info("TTS converted → %s", output)
            return f"Speech → {output} ({audio_format.upper()}, {speed}x speed)"

        except Exception as exc:
            logger.error("TTS failed: %s", exc)
            return f"Error: {exc}"
