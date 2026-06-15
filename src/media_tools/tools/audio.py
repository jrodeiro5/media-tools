"""Audio manipulation toolkit — convert, trim, fade, speed, info."""

from __future__ import annotations

from pathlib import Path

import pydub

from media_tools.utils import logger, validate_input, validate_output_dir


class AudioToolkit:
    name = "audio"

    @staticmethod
    def convert(input_path: str, output: str, bitrate: str = "192k") -> str:
        """Convert audio between formats."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            ext = Path(output).suffix.lower().lstrip(".")
            audio = pydub.AudioSegment.from_file(input_path)
            audio.export(output, format=ext, bitrate=bitrate)
            logger.info("Converted audio → %s (bitrate=%s)", output, bitrate)
        except Exception as exc:
            logger.error("convert failed: %s", exc)
            return f"Error: {exc}"

        return f"Converted to {output}"

    @staticmethod
    def trim(input_path: str, output: str, start_ms: int = 0, end_ms: int = 0) -> str:
        """Trim audio by milliseconds."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            audio = pydub.AudioSegment.from_file(input_path)
            if end_ms > 0:
                audio = audio[start_ms:end_ms]
            else:
                audio = audio[start_ms:]
            ext = Path(output).suffix.lower().lstrip(".")
            audio.export(output, format=ext)
            duration = len(audio) / 1000
            logger.info("Trimmed audio %ds → %s", duration, output)
        except Exception as exc:
            logger.error("trim failed: %s", exc)
            return f"Error: {exc}"

        return f"Trimmed {duration:.1f}s → {output}"

    @staticmethod
    def fade(input_path: str, output: str, fade_in_ms: int = 1000, fade_out_ms: int = 2000) -> str:
        """Add fade-in and fade-out effects."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            audio = pydub.AudioSegment.from_file(input_path)
            audio = audio.fade_in(fade_in_ms).fade_out(fade_out_ms)
            ext = Path(output).suffix.lower().lstrip(".")
            audio.export(output, format=ext)
            logger.info("Faded audio → %s (in=%dms, out=%dms)", output, fade_in_ms, fade_out_ms)
        except Exception as exc:
            logger.error("fade failed: %s", exc)
            return f"Error: {exc}"

        return f"Faded → {output}"

    @staticmethod
    def speed(input_path: str, output: str, factor: float = 1.5) -> str:
        """Change audio playback speed."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            audio = pydub.AudioSegment.from_file(input_path)
            new_rate = int(audio.frame_rate * factor)
            audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_rate})
            audio = audio.set_frame_rate(audio.frame_rate)
            ext = Path(output).suffix.lower().lstrip(".")
            audio.export(output, format=ext)
            logger.info("Speed changed to %sx → %s", factor, output)
        except Exception as exc:
            logger.error("speed failed: %s", exc)
            return f"Error: {exc}"

        return f"Speed {factor}x → {output}"

    @staticmethod
    def info(input_path: str) -> str:
        """Get audio metadata."""
        err = validate_input(input_path)
        if err:
            return err

        try:
            audio = pydub.AudioSegment.from_file(input_path)
            duration = len(audio) / 1000
            size_mb = Path(input_path).stat().st_size / (1024 * 1024)
            return (
                f"Duration: {duration:.1f}s\n"
                f"Channels: {audio.channels}\n"
                f"Sample rate: {audio.frame_rate} Hz\n"
                f"Sample width: {audio.sample_width} bytes\n"
                f"File size: {size_mb:.2f} MB"
            )
        except Exception as exc:
            logger.error("info failed: %s", exc)
            return f"Error: {exc}"
