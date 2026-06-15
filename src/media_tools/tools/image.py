"""Image manipulation toolkit — convert, resize, compress, crop, info."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter

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
    def rotate(input_path: str, output: str, angle: int = 90) -> str:
        """Rotate image by angle (90, 180, 270)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if angle not in (90, 180, 270):
            return "Error: angle must be 90, 180, or 270"

        try:
            img = Image.open(input_path)
            img = img.rotate(angle, expand=True)
            img.save(output)
            logger.info("Rotated %d° → %s", angle, output)
        except Exception as exc:
            logger.error("rotate failed: %s", exc)
            return f"Error: {exc}"

        return f"Rotated {angle}° → {output}"

    @staticmethod
    def flip(input_path: str, output: str, direction: str = "horizontal") -> str:
        """Flip image horizontally or vertically."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if direction not in ("horizontal", "vertical"):
            return "Error: direction must be 'horizontal' or 'vertical'"

        try:
            img = Image.open(input_path)
            if direction == "horizontal":
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            img.save(output)
            logger.info("Flipped %s → %s", direction, output)
        except Exception as exc:
            logger.error("flip failed: %s", exc)
            return f"Error: {exc}"

        return f"Flipped {direction} → {output}"

    @staticmethod
    def text_overlay(
        input_path: str,
        output: str,
        text: str,
        position: str = "bottom-right",
        font_size: int = 24,
        color: str = "#ffffff",
        stroke_color: str = "#000000",
        stroke_width: int = 2,
        margin: int = 10,
    ) -> str:
        """Add text overlay to an image."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from PIL import ImageDraw, ImageFont

            img = Image.open(input_path).convert("RGBA")
            txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_layer)

            # Try to load a font, fall back to default
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", font_size)
                except (OSError, IOError):
                    font = ImageFont.load_default()

            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            # Position
            w, h = img.size
            if "left" in position:
                x = margin
            elif "right" in position:
                x = w - text_w - margin
            else:
                x = (w - text_w) // 2

            if "top" in position:
                y = margin
            elif "bottom" in position:
                y = h - text_h - margin
            else:
                y = (h - text_h) // 2

            # Draw stroke (outline)
            for dx in (-stroke_width, -stroke_width, 0, stroke_width, stroke_width, stroke_width, 0, -stroke_width):
                for dy in (-stroke_width, 0, stroke_width, 0, -stroke_width, stroke_width, -stroke_width, stroke_width):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
            # Draw text
            draw.text((x, y), text, font=font, fill=color)

            img = Image.alpha_composite(img, txt_layer)
            ext = Path(output).suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg"):
                img = img.convert("RGB")
            img.save(output)
            logger.info("Text overlay → %s", output)
        except Exception as exc:
            logger.error("text_overlay failed: %s", exc)
            return f"Error: {exc}"

        return f"Text overlay → {output}"

    @staticmethod
    def border(
        input_path: str,
        output: str,
        width: int = 10,
        color: str = "#ffffff",
    ) -> str:
        """Add a border/frame to an image."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            img = Image.open(input_path)
            new_w = img.width + 2 * width
            new_h = img.height + 2 * width

            if img.mode == "RGBA":
                new_img = Image.new("RGBA", (new_w, new_h), color + "ff")
            else:
                new_img = Image.new(img.mode, (new_w, new_h), color)
            new_img.paste(img, (width, width))
            new_img.save(output)
            logger.info("Border %dpx → %s", width, output)
        except Exception as exc:
            logger.error("border failed: %s", exc)
            return f"Error: {exc}"

        return f"Border {width}px → {output}"

    @staticmethod
    def merge(
        input_paths: list[str],
        output: str,
        direction: str = "horizontal",
    ) -> str:
        """Merge images side-by-side (horizontal) or stacked (vertical)."""
        for f in input_paths:
            err = validate_input(f)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err
        if direction not in ("horizontal", "vertical"):
            return "Error: direction must be 'horizontal' or 'vertical'"

        try:
            images = [Image.open(f) for f in input_paths]
            # Convert to same mode
            mode = images[0].mode
            images = [img.convert(mode) for img in images]

            if direction == "horizontal":
                total_w = sum(img.width for img in images)
                max_h = max(img.height for img in images)
                new_img = Image.new(mode, (total_w, max_h))
                x_offset = 0
                for img in images:
                    new_img.paste(img, (x_offset, 0))
                    x_offset += img.width
            else:
                max_w = max(img.width for img in images)
                total_h = sum(img.height for img in images)
                new_img = Image.new(mode, (max_w, total_h))
                y_offset = 0
                for img in images:
                    new_img.paste(img, (0, y_offset))
                    y_offset += img.height

            new_img.save(output)
            logger.info("Merged %d images → %s", len(images), output)
        except Exception as exc:
            logger.error("merge failed: %s", exc)
            return f"Error: {exc}"

        return f"Merged {len(input_paths)} images → {output}"

    @staticmethod
    def blur(input_path: str, output: str, radius: float = 5.0) -> str:
        """Apply blur filter to an image."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            img = Image.open(input_path)
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            img.save(output)
            logger.info("Blur radius=%.1f → %s", radius, output)
        except Exception as exc:
            logger.error("blur failed: %s", exc)
            return f"Error: {exc}"

        return f"Blur (r={radius}) → {output}"

    @staticmethod
    def ocr(input_path: str) -> str:
        """Extract text from image using pytesseract."""
        err = validate_input(input_path)
        if err:
            return err

        try:
            import pytesseract
            img = Image.open(input_path)
            text = pytesseract.image_to_string(img)
            text = text.strip()
            logger.info("OCR → %d chars", len(text))
            return text if text else "No text found in image"
        except ImportError:
            return "Error: pytesseract not installed. Run: pip install pytesseract"
        except Exception as exc:
            logger.error("ocr failed: %s", exc)
            return f"Error: {exc}"

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
