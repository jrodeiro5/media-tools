"""Image manipulation toolkit — convert, resize, compress, crop, info."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter

from media_tools.utils import logger, validate_input, validate_output_dir

SUPPORTED_FORMATS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
    "bmp",
    "tiff",
    "ico",
    "heic",
    "heif",
    "avif",
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
            supported = ", ".join(sorted(SUPPORTED_FORMATS))
            msg = f"unsupported output format '{ext}' — supported: {supported}"
            logger.warning(msg)
            return f"Error: {msg}"

        try:
            img: Image.Image = Image.open(input_path)
            if img.mode in ("RGBA", "P") and ext in ("jpg", "jpeg"):
                img = img.convert("RGB")
            save_kwargs: dict[str, Any] = {"quality": quality} if ext in ("jpg", "jpeg", "webp") else {}
            img.save(output, **save_kwargs)
        except Exception as exc:
            logger.error("convert failed: %s", exc)
            return f"Error: {exc}"

        return f"Converted to {output}"

    @staticmethod
    def resize(
        input_path: str,
        output: str,
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
            img: Image.Image = Image.open(input_path)
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

            img = img.resize((int(width or 0), int(height or 0)), Image.Resampling.LANCZOS)
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
            img: Image.Image = Image.open(input_path)
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
            img: Image.Image = Image.open(input_path)
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
            img: Image.Image = Image.open(input_path)
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
            img: Image.Image = Image.open(input_path)
            if direction == "horizontal":
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            else:
                img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
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

            img: Image.Image = Image.open(input_path).convert("RGBA")
            txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_layer)

            # Try to load a font, fall back to default
            try:
                font: ImageFont.FreeTypeFont | ImageFont.ImageFont = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", font_size
                )
            except OSError:
                try:
                    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", font_size)
                except OSError:
                    font = ImageFont.load_default()

            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            # Position
            w, h = img.size
            if "left" in position:
                x: float = margin
            elif "right" in position:
                x = w - text_w - margin
            else:
                x = (w - text_w) // 2

            if "top" in position:
                y: float = margin
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
            img: Image.Image = Image.open(input_path)
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
            images: list[Image.Image] = [Image.open(f) for f in input_paths]
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
    def watermark(
        input_path: str,
        watermark_path: str,
        output: str,
        position: str = "bottom-right",
        margin: int = 10,
        opacity: float = 1.0,
    ) -> str:
        """Overlay a watermark image onto another image."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_input(watermark_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if not 0.0 <= opacity <= 1.0:
            return "Error: opacity must be between 0.0 and 1.0"

        try:
            base = Image.open(input_path).convert("RGBA")
            mark = Image.open(watermark_path).convert("RGBA")

            if opacity < 1.0:
                alpha = mark.getchannel("A").point(lambda a: int(a * opacity))
                mark.putalpha(alpha)

            positions = {
                "top-left": (margin, margin),
                "top-right": (base.width - mark.width - margin, margin),
                "bottom-left": (margin, base.height - mark.height - margin),
                "bottom-right": (base.width - mark.width - margin, base.height - mark.height - margin),
                "center": ((base.width - mark.width) // 2, (base.height - mark.height) // 2),
            }
            xy = positions.get(position)
            if xy is None:
                return f"Error: position must be one of {list(positions)}"

            base.alpha_composite(mark, dest=xy)
            if Path(output).suffix.lower() in (".jpg", ".jpeg"):
                base = base.convert("RGB")
            base.save(output)
            logger.info("Watermarked → %s", output)
        except Exception as exc:
            logger.error("watermark failed: %s", exc)
            return f"Error: {exc}"

        return f"Watermarked → {output}"

    @staticmethod
    def apply_brand_kit(
        input_path: str,
        output: str,
        font_path: str | None = None,
        color: str | None = None,
        logo_path: str | None = None,
        logo_position: str = "bottom-right",
        logo_scale: float = 0.15,
    ) -> str:
        """Apply an offline brand kit: optional color band + logo corner paste (PIL only).

        font_path is accepted for API parity with md_to_branded_pdf; S7 draws no
        text so it has no visual effect here.
        """
        import json

        from PIL import ImageColor, ImageDraw

        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if not color and not logo_path:
            return "Error: specify color and/or logo_path"
        if logo_path:
            err = validate_input(logo_path)
            if err:
                return err
        if not 0.0 < logo_scale <= 1.0:
            return "Error: logo_scale must be between 0.0 and 1.0"

        try:
            applied: list[str] = []
            img: Image.Image = Image.open(input_path).convert("RGBA")

            if color:
                try:
                    rgb = ImageColor.getcolor(color, "RGB")
                except ValueError:
                    return f"Error: invalid color '{color}' (use #rrggbb)"
                band_h = max(1, int(img.height * 0.08))
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, img.height - band_h, img.width, img.height], fill=rgb)
                applied.append(f"color_band:{color}")

            if logo_path:
                logo = Image.open(logo_path).convert("RGBA")
                target_w = max(1, int(img.width * logo_scale))
                ratio = target_w / logo.width
                logo = logo.resize((target_w, max(1, int(logo.height * ratio))), Image.Resampling.LANCZOS)
                margin = 10
                positions = {
                    "top-left": (margin, margin),
                    "top-right": (img.width - logo.width - margin, margin),
                    "bottom-left": (margin, img.height - logo.height - margin),
                    "bottom-right": (
                        img.width - logo.width - margin,
                        img.height - logo.height - margin,
                    ),
                    "center": ((img.width - logo.width) // 2, (img.height - logo.height) // 2),
                }
                xy = positions.get(logo_position)
                if xy is None:
                    return f"Error: logo_position must be one of {list(positions)}"
                img.alpha_composite(logo, dest=xy)
                applied.append(f"logo:{logo_position}")

            ext = Path(output).suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg"):
                img = img.convert("RGB")
            img.save(output)
            logger.info("Brand kit → %s (%s)", output, ", ".join(applied))
        except Exception as exc:
            logger.error("apply_brand_kit failed: %s", exc)
            return f"Error: {exc}"

        return json.dumps({"output": output, "applied": applied}, ensure_ascii=False)

    @staticmethod
    def collage(
        input_paths: list[str],
        output: str,
        columns: int = 2,
        cell_size: int = 300,
        spacing: int = 5,
        background: str = "#ffffff",
    ) -> str:
        """Arrange images into a fixed-size grid collage."""
        for f in input_paths:
            err = validate_input(f)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err
        if not input_paths:
            return "Error: no input images provided"

        try:
            rows = (len(input_paths) + columns - 1) // columns
            grid_w = columns * cell_size + (columns + 1) * spacing
            grid_h = rows * cell_size + (rows + 1) * spacing
            canvas = Image.new("RGB", (grid_w, grid_h), background)

            for idx, path in enumerate(input_paths):
                img: Image.Image = Image.open(path).convert("RGB")
                img.thumbnail((cell_size, cell_size))
                col, row = idx % columns, idx // columns
                cell_x = spacing + col * (cell_size + spacing)
                cell_y = spacing + row * (cell_size + spacing)
                paste_x = cell_x + (cell_size - img.width) // 2
                paste_y = cell_y + (cell_size - img.height) // 2
                canvas.paste(img, (paste_x, paste_y))

            canvas.save(output)
            logger.info("Collage %dx%d → %s", columns, rows, output)
        except Exception as exc:
            logger.error("collage failed: %s", exc)
            return f"Error: {exc}"

        return f"Collage ({len(input_paths)} images, {columns} cols) → {output}"

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
            img: Image.Image = Image.open(input_path)
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

            img: Image.Image = Image.open(input_path)
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
            img: Image.Image = Image.open(input_path)
            size_mb = Path(input_path).stat().st_size / (1024 * 1024)
            return (
                f"Format: {img.format}\nMode: {img.mode}\nSize: {img.width}x{img.height}\nFile size: {size_mb:.2f} MB"
            )
        except Exception as exc:
            logger.error("info failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def export_social_pack(src: str, out_dir: str, mode: str = "center-crop") -> str:
        """Export 9:16 / 1:1 / 16:9 variants of one image (Canva-style multi-ratio, offline).

        Decodes once (PIL + EXIF transpose), saves each variant from the same
        in-memory buffer in one loop. Targets are 1080x1920 / 1080x1080 /
        1920x1080, but content is NEVER upscaled past source resolution —
        small sources yield smaller (aspect-correct) files, reported honestly.

        mode 'center-crop': crop to the target aspect first, then scale down.
        mode 'letterbox': scale-to-fit then pad with black to the exact target.

        LOAD-BEARING RISK: naive center-crop can decapitate faces/subjects —
        it cuts symmetric edges with no saliency awareness. Smart-focal
        detection is a future upgrade, not this method.
        """
        import json

        from PIL import ImageOps

        err = validate_input(src)
        if err:
            return err
        err = validate_output_dir(out_dir)
        if err:
            return err
        if mode not in ("center-crop", "letterbox"):
            return "Error: mode must be 'center-crop' or 'letterbox'"

        targets = {"9x16": (1080, 1920), "1x1": (1080, 1080), "16x9": (1920, 1080)}

        try:
            img: Image.Image = ImageOps.exif_transpose(Image.open(src))
            img.load()
            sw, sh = img.size
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            suffix = Path(src).suffix or ".jpg"
            ext = suffix.lower().lstrip(".")
            save_kwargs: dict[str, Any] = {"quality": 85} if ext in ("jpg", "jpeg", "webp") else {}

            variants: list[dict[str, object]] = []
            for label, (tw, th) in targets.items():
                aspect = tw / th
                if mode == "center-crop":
                    if sw / sh > aspect:
                        cw, ch = int(sh * aspect), sh
                    else:
                        cw, ch = sw, int(sw / aspect)
                    left, top = (sw - cw) // 2, (sh - ch) // 2
                    frame = img.crop((left, top, left + cw, top + ch))
                    scale = min(1.0, tw / cw, th / ch)
                    ow, oh = max(1, int(cw * scale)), max(1, int(ch * scale))
                    if scale < 1.0:
                        frame = frame.resize((ow, oh), Image.Resampling.LANCZOS)
                else:
                    scale = min(1.0, tw / sw, th / sh)
                    ow_s, oh_s = max(1, int(sw * scale)), max(1, int(sh * scale))
                    frame = img.resize((ow_s, oh_s), Image.Resampling.LANCZOS) if scale < 1.0 else img.copy()
                    ow, oh = tw, th
                    canvas = Image.new(frame.mode, (ow, oh), (0, 0, 0))
                    canvas.paste(frame, ((ow - ow_s) // 2, (oh - oh_s) // 2))
                    frame = canvas
                dest = str(out / f"{Path(src).stem}_{label}{suffix}")
                save_img = frame.convert("RGB") if ext in ("jpg", "jpeg") and frame.mode != "RGB" else frame
                save_img.save(dest, **save_kwargs)
                variants.append({"label": label, "path": dest, "width": ow, "height": oh})

            logger.info("Social pack (%s) → %s (%d variants)", mode, out_dir, len(variants))
        except Exception as exc:
            logger.error("export_social_pack failed: %s", exc)
            return f"Error: {exc}"

        return json.dumps({"mode": mode, "source": src, "variants": variants}, ensure_ascii=False)

    @staticmethod
    def remove_background(input_path: str, output: str, alpha_matting: bool = False) -> str:
        """Remove background from an image using U2-Net AI model.

        Uses rembg library with U2-Net model for salient object detection.
        First run downloads model (~100MB), subsequent runs use cached model.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from rembg import remove

            img: Image.Image = Image.open(input_path)
            result = remove(img, alpha_matting=alpha_matting)

            ext = Path(output).suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg") and result.mode == "RGBA":
                result = result.convert("RGB")

            result.save(output)
            logger.info("Removed background → %s", output)
        except ImportError:
            return "Error: rembg not installed. Run: pip install rembg"
        except SystemExit as exc:
            detail = exc.code or "rembg exited (likely missing onnxruntime backend)"
            logger.error("remove_background failed: %s", detail)
            return f"Error: rembg backend missing (onnxruntime): {detail}"
        except Exception as exc:
            logger.error("remove_background failed: %s", exc)
            return f"Error: {exc}"

        return f"Background removed → {output}"

    @staticmethod
    def grayscale(input_path: str, output: str) -> str:
        """Convert an image to grayscale (mode L)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            img: Image.Image = Image.open(input_path)
            img = img.convert("L")
            ext = Path(output).suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg") and img.mode != "L":
                img = img.convert("L")
            img.save(output)
            logger.info("Grayscale → %s", output)
        except Exception as exc:
            logger.error("grayscale failed: %s", exc)
            return f"Error: {exc}"

        return f"Grayscale → {output}"

    @staticmethod
    def sharpen(input_path: str, output: str, radius: float = 2.0, percent: int = 150, threshold: int = 3) -> str:
        """Sharpen an image with an unsharp mask (sensible defaults)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            img: Image.Image = Image.open(input_path)
            img = img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
            img.save(output)
            logger.info("Sharpen r=%.1f p=%d t=%d → %s", radius, percent, threshold, output)
        except Exception as exc:
            logger.error("sharpen failed: %s", exc)
            return f"Error: {exc}"

        return f"Sharpened → {output}"

    @staticmethod
    def circle_crop(input_path: str, output: str) -> str:
        """Center-crop an image to a circle; corners stay transparent (RGBA)."""
        from PIL import ImageDraw

        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            img: Image.Image = Image.open(input_path).convert("RGBA")
            side = min(img.width, img.height)
            left, top = (img.width - side) // 2, (img.height - side) // 2
            img = img.crop((left, top, left + side, top + side))
            mask = Image.new("L", (side, side), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, side, side), fill=255)
            img.putalpha(mask)
            ext = Path(output).suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg"):
                img = img.convert("RGB")
            img.save(output)
            logger.info("Circle crop → %s", output)
        except Exception as exc:
            logger.error("circle_crop failed: %s", exc)
            return f"Error: {exc}"

        return f"Circle crop → {output}"

    @staticmethod
    def split_tiles(input_path: str, output_dir: str, rows: int = 2, cols: int = 2) -> str:
        """Split an image into a rows×cols tile grid + sidecar JSON manifest."""
        import json

        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_dir)
        if err:
            return err
        if rows < 1 or cols < 1:
            return "Error: rows and cols must be >= 1"

        try:
            img: Image.Image = Image.open(input_path)
            img.load()
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            stem = Path(input_path).stem
            tw, th = img.width // cols, img.height // rows
            files: list[dict[str, object]] = []
            for r in range(rows):
                for c in range(cols):
                    left, top = c * tw, r * th
                    right = (c + 1) * tw if c < cols - 1 else img.width
                    bottom = (r + 1) * th if r < rows - 1 else img.height
                    tile = img.crop((left, top, right, bottom))
                    dest = str(out_dir / f"{stem}_tile_{r:02d}_{c:02d}.png")
                    tile.save(dest)
                    files.append({"row": r, "col": c, "path": dest, "width": right - left, "height": bottom - top})
            payload = {"source": input_path, "rows": rows, "cols": cols, "tiles": len(files), "files": files}
            manifest = str(out_dir / f"{stem}_tiles_manifest.json")
            Path(manifest).write_text(json.dumps(payload, indent=2), encoding="utf-8")
            payload["manifest"] = manifest
            logger.info("Split %dx%d tiles → %s", rows, cols, output_dir)
        except Exception as exc:
            logger.error("split_tiles failed: %s", exc)
            return f"Error: {exc}"

        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def upscale(input_path: str, output: str, scale: int = 2) -> str:
        """Upscale an image 2x/3x with FSRCNN-small via cv2.dnn_superres.

        Model (~10KB) downloads on first run to ~/.cache/media-tools/models
        (SHA256-pinned, rembg precedent); no cached model + no network
        returns an offline Error. Model source Saafke/FSRCNN_Tensorflow
        is Apache-2.0.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if scale not in (2, 3):
            return "Error: scale must be 2 or 3 (FSRCNN-small ships x2/x3)"

        try:
            import cv2

            from media_tools.tools._vision import ensure_asset

            model_path = ensure_asset(f"fsrcnn_x{scale}")
            sr = cv2.dnn_superres.DnnSuperResImpl.create()
            sr.readModel(model_path)
            sr.setModel("fsrcnn", scale)
            img = cv2.imread(input_path)
            if img is None:
                return f"Error: could not decode image: {input_path}"
            cv2.imwrite(output, sr.upsample(img))
            logger.info("Upscaled x%d → %s", scale, output)
        except RuntimeError as exc:
            return str(exc)
        except Exception as exc:
            logger.error("upscale failed: %s", exc)
            return f"Error: {exc}"

        return f"Upscaled x{scale} → {output}"

    @staticmethod
    def blur_faces(input_path: str, output: str, mode: str = "pixelate") -> str:
        """Obscure faces with the Haar frontal cascade (pixelate default, else blur).

        Haar limits: finds near-upright frontal faces >= 30px; misses
        profiles, heavy occlusion, tiny or rotated faces. Obscuring is
        best-effort, not a privacy guarantee — verify the output.
        Zero faces is success: the output is still written (a copy) and
        the message reports faces:0.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if mode not in ("pixelate", "blur"):
            return "Error: mode must be 'pixelate' or 'blur'"

        try:
            import cv2

            from media_tools.tools._vision import detect_faces, ensure_asset, obscure_boxes

            xml_path = ensure_asset("haar_frontalface")
            img = cv2.imread(input_path)
            if img is None:
                return f"Error: could not decode image: {input_path}"
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detect_faces(gray, xml_path)
            obscure_boxes(img, faces, mode)
            cv2.imwrite(output, img)
            logger.info("Blurred %d faces (%s) → %s", len(faces), mode, output)
        except RuntimeError as exc:
            return str(exc)
        except Exception as exc:
            logger.error("blur_faces failed: %s", exc)
            return f"Error: {exc}"

        return f"Blurred {len(faces)} faces ({mode}) → {output}"
