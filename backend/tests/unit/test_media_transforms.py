"""Unit tests for image transformation functions."""

from io import BytesIO

import pytest
from PIL import Image

from app.services.media import extract_dominant_colors, transform_image


@pytest.fixture
def rgb_image_bytes():
    """800x600 RGB JPEG image."""
    img = Image.new("RGB", (800, 600), color="blue")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def rgba_image_bytes():
    """400x300 RGBA PNG image."""
    img = Image.new("RGBA", (400, 300), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def multicolor_image_bytes():
    """Image with multiple distinct color blocks for dominant color testing."""
    img = Image.new("RGB", (300, 300), color="red")
    for x in range(150, 300):
        for y in range(0, 150):
            img.putpixel((x, y), (0, 0, 255))
    for x in range(0, 150):
        for y in range(150, 300):
            img.putpixel((x, y), (0, 255, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestTransformImageResize:
    def test_resize_width_only(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, width=400)
        img = Image.open(BytesIO(data))
        assert img.width == 400

    def test_resize_height_only(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, height=300)
        img = Image.open(BytesIO(data))
        assert img.height == 300

    def test_resize_both_dimensions(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, width=200, height=200, fit="fill")
        img = Image.open(BytesIO(data))
        assert img.size == (200, 200)

    def test_fit_contain(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, width=200, height=200, fit="contain")
        img = Image.open(BytesIO(data))
        assert img.width <= 200
        assert img.height <= 200

    def test_fit_cover(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, width=200, height=200, fit="cover")
        img = Image.open(BytesIO(data))
        assert img.size == (200, 200)

    def test_fit_fill_stretches(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, width=100, height=400, fit="fill")
        img = Image.open(BytesIO(data))
        assert img.size == (100, 400)


class TestTransformImageCrop:
    def test_basic_crop(self, rgb_image_bytes):
        crop = {"x": 100, "y": 100, "width": 200, "height": 150}
        data, ct = transform_image(rgb_image_bytes, crop=crop)
        img = Image.open(BytesIO(data))
        assert img.size == (200, 150)

    def test_crop_then_resize(self, rgb_image_bytes):
        crop = {"x": 0, "y": 0, "width": 400, "height": 300}
        data, ct = transform_image(rgb_image_bytes, width=100, height=100, crop=crop, fit="fill")
        img = Image.open(BytesIO(data))
        assert img.size == (100, 100)


class TestTransformImageRotate:
    def test_rotate_90(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, rotate=90)
        img = Image.open(BytesIO(data))
        assert img.width == 600
        assert img.height == 800

    def test_rotate_180(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, rotate=180)
        img = Image.open(BytesIO(data))
        assert img.width == 800
        assert img.height == 600


class TestTransformImageFormatConversion:
    def test_jpeg_to_png(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, format="png")
        assert ct == "image/png"
        img = Image.open(BytesIO(data))
        assert img.format == "PNG"

    def test_png_to_jpeg(self, rgba_image_bytes):
        data, ct = transform_image(rgba_image_bytes, format="jpeg")
        assert ct == "image/jpeg"
        img = Image.open(BytesIO(data))
        assert img.format == "JPEG"
        assert img.mode == "RGB"

    def test_to_webp(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, format="webp")
        assert ct == "image/webp"
        img = Image.open(BytesIO(data))
        assert img.format == "WEBP"

    def test_default_format_is_jpeg(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes)
        assert ct == "image/jpeg"


class TestTransformImageQuality:
    def test_low_quality_smaller_size(self, rgb_image_bytes):
        high_q, _ = transform_image(rgb_image_bytes, quality=95, format="jpeg")
        low_q, _ = transform_image(rgb_image_bytes, quality=10, format="jpeg")
        assert len(low_q) < len(high_q)

    def test_quality_produces_valid_image(self, rgb_image_bytes):
        data, ct = transform_image(rgb_image_bytes, quality=50)
        img = Image.open(BytesIO(data))
        assert img.format == "JPEG"


class TestExtractDominantColors:
    def test_returns_correct_count(self, multicolor_image_bytes):
        colors = extract_dominant_colors(multicolor_image_bytes, num_colors=3)
        assert len(colors) == 3

    def test_returns_hex_strings(self, multicolor_image_bytes):
        colors = extract_dominant_colors(multicolor_image_bytes, num_colors=5)
        for c in colors:
            assert c.startswith("#")
            assert len(c) == 7

    def test_default_five_colors(self, rgb_image_bytes):
        colors = extract_dominant_colors(rgb_image_bytes)
        assert len(colors) <= 5
