"""Image manipulation toolkit — convert, resize, compress, crop, info."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from media_tools.utils import logger, validate_input, validate_output_dir

SUPPORTED_FORMATS = {
    "jpg", "jpeg", "png", "webp", "gif", "bmp", "tiff", "ico",
    "heic", "heif", "avif",
}


class ImageToolkit:
    name = "image"

    @staticmethod
    def convert(input_path: str, output: str, quality: int = 85) -> str:
        """Convert an image to another format."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        ext = Path(output).suffix.lower().lstrip(".")
        if ext not in SUPPORTED_FORMATS:
            supported = ', '.join(sorted(SUPPORTED_FORMATS))
            msg = f"unsupported output format '{ext}' — supported: {supported}"
            logger.warning(msg)
            return f"Error: {msg}"

        try:
            img = Image.open(input_path)
            if img.mode in ("RGBA", "P") and ext in ("jpg", "jpeg"):
                img = img.convert("RGB")
            save_kwargs = {"quality": quality} if ext in ("jpg", "jpeg", "webp") else {}
            img.save(output, **save_kwargs)
        except Exception as exc:
            logger.error("convert failed: %s", exc)
            return f"Error: {exc}"

        return f"Converted to {output}"

    @staticmethod
    def resize(
        input_path: str, output: str,
        width: int | None = None,
        height: int | None = None,
        percent: int | None = None,
    ) -> str:
        """Resize an image by pixels or percentage."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        if not any([width, height, percent]):
            return "Error: specify width, height, or percent"

        try:
            img = Image.open(input_path)
            if percent:
                width = int(img.width * percent / 100)
                height = int(img.height * percent / 100)
            elif width and height:
                pass
            elif width:
                ratio = width / img.width
                height = int(img.height * ratio)
            elif height:
                ratio = height / img.height
                width = int(img.width * ratio)

            img = img.resize((width, height), Image.LANCZOS)
            img.save(output)
            logger.info("Resized %dx%d → %s", img.width, img.height, output)
        except Exception as exc:
            logger.error("resize failed: %s", exc)
            return f"Error: {exc}"

        return f"Resized to {width}x{height} → {output}"

    @staticmethod
    def compress(input_path: str, output: str, quality: int = 70) -> str:
        """Compress an image."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            img = Image.open(input_path)
            ext = Path(output).suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg"):
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(output, "JPEG", quality=quality, optimize=True)
            elif ext == "png":
                img.save(output, "PNG", optimize=True)
            elif ext == "webp":
                img.save(output, "WEBP", quality=quality)
            else:
                img.save(output, optimize=True)
            logger.info("Compressed → %s (quality=%d)", output, quality)
        except Exception as exc:
            logger.error("compress failed: %s", exc)
            return f"Error: {exc}"

        return f"Compressed to {output}"

    @staticmethod
    def crop(input_path: str, output: str, left: int, top: int, right: int, bottom: int) -> str:
        """Crop an image by pixel coordinates."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            img = Image.open(input_path)
            # Validate crop bounds
            if left < 0 or top < 0 or right < 0 or bottom < 0:
                return "crop coordinates cannot be negative"
            if left >= right:
                return f"left ({left}) must be less than right ({right})"
            if top >= bottom:
                return f"top ({top}) must be less than bottom ({bottom})"
            if right > img.width:
                return f"right ({right}) exceeds image width ({img.width})"
            if bottom > img.height:
                return f"bottom ({bottom}) exceeds image height ({img.height})"

            img = img.crop((left, top, right, bottom))
            img.save(output)
            logger.info("Cropped → %s", output)
        except Exception as exc:
            logger.error("crop failed: %s", exc)
            return f"Error: {exc}"

        return f"Cropped to {output}"

    @staticmethod
    def info(input_path: str) -> str:
        """Get image metadata."""
        err = validate_input(input_path)
        if err:
            return err

        try:
            img = Image.open(input_path)
            size_mb = Path(input_path).stat().st_size / (1024 * 1024)
            return (
                f"Format: {img.format}\n"
                f"Mode: {img.mode}\n"
                f"Size: {img.width}x{img.height}\n"
                f"File size: {size_mb:.2f} MB"
            )
        except Exception as exc:
            logger.error("info failed: %s", exc)
            return f"Error: {exc}"
