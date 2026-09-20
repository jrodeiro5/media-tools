"""Audio manipulation toolkit — convert, trim, fade, speed, info, chunk."""

from __future__ import annotations

import json
import os
import urllib.request
import uuid
from pathlib import Path

import pydub
from pydub.silence import split_on_silence

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
    def merge(input_paths: list[str], output: str) -> str:
        """Concatenate multiple audio clips in order."""
        for p in input_paths:
            err = validate_input(p)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err
        if not input_paths:
            return "Error: no input audio files provided"

        try:
            combined = pydub.AudioSegment.from_file(input_paths[0])
            for p in input_paths[1:]:
                combined += pydub.AudioSegment.from_file(p)
            ext = Path(output).suffix.lower().lstrip(".")
            combined.export(output, format=ext)
            logger.info("Merged %d clips → %s", len(input_paths), output)
        except Exception as exc:
            logger.error("merge failed: %s", exc)
            return f"Error: {exc}"

        return f"Merged {len(input_paths)} clips → {output}"

    @staticmethod
    def normalize(input_path: str, output: str, target_dbfs: float = -20.0) -> str:
        """Normalize audio volume to a target dBFS level."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            audio = pydub.AudioSegment.from_file(input_path)
            change = target_dbfs - audio.dBFS
            audio = audio.apply_gain(change)
            ext = Path(output).suffix.lower().lstrip(".")
            audio.export(output, format=ext)
            logger.info("Normalized to %.1f dBFS → %s", target_dbfs, output)
        except Exception as exc:
            logger.error("normalize failed: %s", exc)
            return f"Error: {exc}"

        return f"Normalized to {target_dbfs} dBFS → {output}"

    @staticmethod
    def chunk_silence(
        input_path: str,
        output_dir: str,
        min_silence_ms: int = 1000,
        silence_thresh_dbfs: float | None = None,
        keep_ms: int = 200,
        max_chunks: int = 500,
    ) -> str:
        """Split audio on silence into bite-size clips for small-model transcribe.

        Returns a JSON string: chunk files with start offsets/durations
        (so a future transcribe step can reassemble ordered transcripts),
        plus chunk count and total duration. A file with no silence long
        enough to split on returns a single chunk honestly, not an error.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_dir)
        if err:
            return err
        if min_silence_ms <= 0:
            return "Error: min_silence_ms must be positive"
        if keep_ms < 0:
            return "Error: keep_ms must be non-negative"

        try:
            audio = pydub.AudioSegment.from_file(input_path)
            total_ms = len(audio)
            thresh = int(audio.dBFS - 14 if silence_thresh_dbfs is None else silence_thresh_dbfs)
            keep = min(keep_ms, total_ms // 2) if total_ms > 0 else 0
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_ms,
                silence_thresh=thresh,
                keep_silence=keep,
            )
            if not chunks:
                chunks = [audio]
            if len(chunks) > max_chunks:
                return (
                    f"Error: would produce {len(chunks)} chunks "
                    f"(max {max_chunks}); raise min_silence_ms or silence_thresh_dbfs"
                )
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            ext = Path(input_path).suffix.lower().lstrip(".") or "wav"
            fmt = ext if ext != "wave" else "wav"
            files: list[dict[str, object]] = []
            offset = 0
            for i, chunk in enumerate(chunks):
                dur_ms = len(chunk)
                name = f"chunk_{i:03d}.{ext}"
                dest = out / name
                chunk.export(str(dest), format=fmt)
                files.append(
                    {
                        "file": str(dest),
                        "index": i,
                        "start_ms": offset,
                        "start_s": round(offset / 1000, 2),
                        "duration_ms": dur_ms,
                        "duration_s": round(dur_ms / 1000, 2),
                    }
                )
                offset += dur_ms
            payload = {
                "chunks": files,
                "chunk_count": len(files),
                "total_duration_ms": total_ms,
                "total_duration_s": round(total_ms / 1000, 2),
                "min_silence_ms": min_silence_ms,
                "silence_thresh_dbfs": thresh,
                "keep_ms": keep,
            }
            logger.info("Split %s on silence → %d chunks in %s", input_path, len(files), output_dir)
        except Exception as exc:
            logger.error("chunk_silence failed: %s", exc)
            return f"Error: {exc}"

        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _stt_endpoint() -> str:
        base = os.environ.get("LITELLM_URL", "http://localhost:4000").rstrip("/")
        return f"{base}/v1/audio/transcriptions"

    @staticmethod
    def _stt_model(model: str | None) -> str:
        return model or os.environ.get("STT_MODEL", "local-whisper-stt")

    @staticmethod
    def _post_transcription(file_path: str, model: str, language: str | None, timeout: int) -> dict[str, object] | str:
        """POST one audio file to the STT endpoint. Returns dict or 'Error: ...'."""
        suffix = Path(file_path).suffix.lower()
        mime = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
        }.get(suffix, "application/octet-stream")
        try:
            audio_bytes = Path(file_path).read_bytes()
        except OSError as exc:
            return f"Error: cannot read {file_path}: {exc}"
        boundary = uuid.uuid4().hex
        body = bytearray()
        fields: dict[str, str] = {"model": model, "response_format": "json"}
        if language:
            fields["language"] = language
        for key, value in fields.items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode()
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{Path(file_path).name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()
            + audio_bytes
            + f"\r\n--{boundary}--\r\n".encode()
        )
        req = urllib.request.Request(
            AudioToolkit._stt_endpoint(),
            data=bytes(body),
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {os.environ.get('LITELLM_API_KEY', 'sk-no-key-required')}",
            },
        )
        # endpoint is AudioToolkit._stt_endpoint(), built from LITELLM_URL env var,
        # not from any tool argument — not attacker-controlled.
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
                raw = resp.read()
        except Exception as exc:
            logger.error("transcribe failed: %s", exc)
            return f"Error: {exc}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("transcribe bad response: %s", exc)
            return f"Error: invalid STT response ({exc})"
        if not isinstance(data, dict):
            return "Error: invalid STT response (expected JSON object)"
        return data

    @staticmethod
    def transcribe(
        input_path: str,
        output: str | None = None,
        model: str | None = None,
        language: str | None = None,
        timeout: int = 300,
    ) -> str:
        """Transcribe speech to text via the local LiteLLM proxy (whisper)."""
        err = validate_input(input_path)
        if err:
            return err
        if output:
            err = validate_output_dir(output)
            if err:
                return err

        resolved = AudioToolkit._stt_model(model)
        data = AudioToolkit._post_transcription(input_path, resolved, language, timeout)
        if isinstance(data, str):
            return data

        payload: dict[str, object] = {
            "input": input_path,
            "model": resolved,
            "text": data.get("text", ""),
        }
        if data.get("segments") is not None:
            payload["segments"] = data["segments"]
        if output:
            try:
                Path(output).write_text(str(payload["text"]))
            except OSError as exc:
                logger.error("transcribe write failed: %s", exc)
                return f"Error: cannot write {output}: {exc}"
            payload["output"] = output
            logger.info("Transcribed %s → %s", input_path, output)
        else:
            logger.info("Transcribed %s", input_path)
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def transcribe_chunks(
        input_path: str,
        out_dir: str,
        model: str | None = None,
        language: str | None = None,
        min_silence_ms: int = 1000,
        silence_thresh_dbfs: float | None = None,
        keep_ms: int = 200,
        max_chunks: int = 500,
        timeout: int = 300,
    ) -> str:
        """Chunk on silence, transcribe each chunk in order, reassemble one transcript."""
        if max_chunks <= 0:
            return "Error: max_chunks must be positive"
        raw = AudioToolkit.chunk_silence(input_path, out_dir, min_silence_ms, silence_thresh_dbfs, keep_ms, max_chunks)
        try:
            plan = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw
        if not isinstance(plan, dict) or "chunks" not in plan:
            return raw

        resolved = AudioToolkit._stt_model(model)
        segments: list[dict[str, object]] = []
        failed: list[dict[str, object]] = []
        for chunk in plan["chunks"]:
            data = AudioToolkit._post_transcription(chunk["file"], resolved, language, timeout)
            if isinstance(data, str):
                failed.append({"index": chunk["index"], "file": chunk["file"], "error": data})
                text = ""
            else:
                text = str(data.get("text", ""))
            segments.append(
                {
                    "index": chunk["index"],
                    "file": chunk["file"],
                    "start_ms": chunk["start_ms"],
                    "start_s": chunk["start_s"],
                    "duration_ms": chunk["duration_ms"],
                    "text": text,
                }
            )
        full_text = "\n".join(str(s["text"]) for s in segments if s["text"])
        out = Path(out_dir)
        transcript_json = str(out / "transcript.json")
        transcript_txt = str(out / "transcript.txt")
        try:
            Path(transcript_json).write_text(json.dumps({"segments": segments, "text": full_text}, ensure_ascii=False))
            Path(transcript_txt).write_text(full_text)
        except OSError as exc:
            logger.error("transcribe_chunks write failed: %s", exc)
            return f"Error: cannot write transcript in {out_dir}: {exc}"
        logger.info("Transcribed %d chunks → %s", len(segments), out_dir)
        return json.dumps(
            {
                "chunk_count": len(segments),
                "failed_chunks": failed,
                "model": resolved,
                "segments": segments,
                "transcript_json": transcript_json,
                "transcript_txt": transcript_txt,
                "total_chars": len(full_text),
            },
            ensure_ascii=False,
        )

    @staticmethod
    def pad_to_duration(input_path: str, output: str, target_ms: int, position: str = "end") -> str:
        """Pad audio with generated silence to reach exactly target_ms (Descript-style, offline).

        One pydub concat — no time-stretching, original samples untouched.
        position 'end' appends (default), 'start' prepends, 'middle' splits
        the silence half/half around the content. Input already >= target is
        returned unchanged with an honest note, not an error.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if target_ms <= 0:
            return "Error: target_ms must be positive"
        if target_ms > 3_600_000:
            return "Error: target_ms capped at 3600000 (1h) — refusing unbounded file"
        if position not in ("end", "start", "middle"):
            return "Error: position must be 'end', 'start', or 'middle'"

        try:
            audio = pydub.AudioSegment.from_file(input_path)
            current_ms = len(audio)
            if current_ms >= target_ms:
                ext = Path(output).suffix.lower().lstrip(".")
                audio.export(output, format=ext)
                payload = {
                    "output": output,
                    "input_ms": current_ms,
                    "target_ms": target_ms,
                    "output_ms": current_ms,
                    "padded": False,
                    "note": f"input already {current_ms}ms >= target {target_ms}ms — returned unchanged",
                }
                logger.info("pad_to_duration no-op: %s already %dms", input_path, current_ms)
                return json.dumps(payload, ensure_ascii=False)
            gap = target_ms - current_ms
            silence = pydub.AudioSegment.silent(duration=gap, frame_rate=audio.frame_rate)
            silence = silence.set_channels(audio.channels).set_sample_width(audio.sample_width)
            if position == "end":
                out = audio + silence
            elif position == "start":
                out = silence + audio
            else:
                half = gap // 2
                pre = silence[:half]
                post = silence[half:]
                out = pre + audio + post
            ext = Path(output).suffix.lower().lstrip(".")
            out.export(output, format=ext)
            payload = {
                "output": output,
                "input_ms": current_ms,
                "target_ms": target_ms,
                "output_ms": len(out),
                "padded": True,
                "position": position,
            }
            logger.info("Padded %dms → %dms (%s) → %s", current_ms, len(out), position, output)
        except Exception as exc:
            logger.error("pad_to_duration failed: %s", exc)
            return f"Error: {exc}"

        return json.dumps(payload, ensure_ascii=False)

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
