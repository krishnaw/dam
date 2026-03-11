import hashlib
from io import BytesIO

from PIL import Image, ImageOps


def generate_thumbnail(
    file_data: bytes, content_type: str, size: tuple[int, int] = (300, 300)
) -> bytes:
    """Generate a thumbnail from image data."""
    img = Image.open(BytesIO(file_data))
    img.thumbnail(size, Image.Resampling.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    output = BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()


def extract_image_dimensions(file_data: bytes) -> tuple[int, int] | None:
    """Extract width and height from image data."""
    try:
        img = Image.open(BytesIO(file_data))
        return img.size
    except Exception:
        return None


def detect_content_type(file_data: bytes) -> str:
    """Detect MIME type using python-magic."""
    try:
        import magic

        return magic.from_buffer(file_data, mime=True)
    except ImportError:
        # Fallback if python-magic not available
        return "application/octet-stream"


def compute_checksum(file_data: bytes) -> str:
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(file_data).hexdigest()


def transform_image(
    file_data: bytes,
    width: int | None = None,
    height: int | None = None,
    fit: str = "cover",
    format: str | None = None,
    quality: int = 85,
    crop: dict | None = None,
    rotate: int | None = None,
) -> tuple[bytes, str]:
    """Apply transformations to image. Returns (transformed_bytes, content_type)."""
    img = Image.open(BytesIO(file_data))

    # Convert RGBA to RGB for JPEG output
    if img.mode == "RGBA" and (format or "").lower() in ("jpeg", "jpg"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg

    # Rotate
    if rotate:
        img = img.rotate(-rotate, expand=True)

    # Crop
    if crop:
        img = img.crop((
            crop["x"], crop["y"],
            crop["x"] + crop["width"], crop["y"] + crop["height"],
        ))

    # Resize
    if width or height:
        img = _resize_image(img, width, height, fit)

    # Output format
    out_format = (format or "jpeg").upper()
    if out_format == "JPG":
        out_format = "JPEG"

    # Ensure RGB mode for JPEG
    if out_format == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    content_type_map = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
        "GIF": "image/gif",
    }

    buf = BytesIO()
    save_kwargs = {}
    if out_format in ("JPEG", "WEBP"):
        save_kwargs["quality"] = quality
    if out_format == "WEBP":
        save_kwargs["method"] = 4
    img.save(buf, format=out_format, **save_kwargs)

    return buf.getvalue(), content_type_map.get(out_format, f"image/{out_format.lower()}")


def _resize_image(
    img: Image.Image, width: int | None, height: int | None, fit: str
) -> Image.Image:
    """Resize image with different fit modes."""
    target_w = width or img.width
    target_h = height or img.height

    if fit == "contain":
        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        return img
    elif fit == "cover":
        return ImageOps.fit(img, (target_w, target_h), Image.Resampling.LANCZOS)
    elif fit == "fill":
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        return img


def extract_dominant_colors(file_data: bytes, num_colors: int = 5) -> list[str]:
    """Extract dominant colors from image. Returns list of hex color strings."""
    img = Image.open(BytesIO(file_data)).convert("RGB")
    img = img.resize((150, 150))

    img_quant = img.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette = img_quant.getpalette()[:num_colors * 3]

    colors = []
    for i in range(0, len(palette), 3):
        r, g, b = palette[i], palette[i + 1], palette[i + 2]
        colors.append(f"#{r:02x}{g:02x}{b:02x}")

    return colors
