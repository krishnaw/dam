"""Unit tests for media service."""

import hashlib
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from app.services.media import (
    compute_checksum,
    detect_content_type,
    extract_image_dimensions,
    generate_thumbnail,
)


@pytest.fixture
def fake_image_bytes():
    """Create a minimal valid PNG image in memory."""
    from PIL import Image

    img = Image.new("RGB", (800, 600), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def fake_rgba_image_bytes():
    """Create a minimal valid RGBA PNG image in memory."""
    from PIL import Image

    img = Image.new("RGBA", (400, 300), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestGenerateThumbnail:
    def test_generates_resized_image(self, fake_image_bytes):
        from PIL import Image

        result = generate_thumbnail(fake_image_bytes, "image/png", size=(300, 300))
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify output is a valid JPEG image
        img = Image.open(BytesIO(result))
        assert img.format == "JPEG"
        assert img.width <= 300
        assert img.height <= 300

    def test_preserves_aspect_ratio(self, fake_image_bytes):
        from PIL import Image

        result = generate_thumbnail(fake_image_bytes, "image/png", size=(300, 300))
        img = Image.open(BytesIO(result))
        # Original is 800x600 (4:3 ratio), thumbnail should preserve ratio
        assert img.width == 300
        assert img.height == 225  # 300 * (600/800)

    def test_converts_rgba_to_rgb(self, fake_rgba_image_bytes):
        from PIL import Image

        result = generate_thumbnail(fake_rgba_image_bytes, "image/png")
        img = Image.open(BytesIO(result))
        assert img.mode == "RGB"


class TestExtractImageDimensions:
    def test_returns_width_height_tuple(self, fake_image_bytes):
        dims = extract_image_dimensions(fake_image_bytes)
        assert dims == (800, 600)

    def test_returns_none_for_invalid_data(self):
        dims = extract_image_dimensions(b"not an image")
        assert dims is None


class TestDetectContentType:
    def test_detect_content_type_with_magic(self):
        mock_magic = MagicMock()
        mock_magic.from_buffer.return_value = "image/png"
        with patch.dict("sys.modules", {"magic": mock_magic}):
            result = detect_content_type(b"fake-png-data")
            mock_magic.from_buffer.assert_called_once_with(b"fake-png-data", mime=True)
            assert result == "image/png"


class TestComputeChecksum:
    def test_known_input_produces_expected_sha256(self):
        data = b"hello world"
        expected = hashlib.sha256(data).hexdigest()
        assert compute_checksum(data) == expected

    def test_deterministic(self):
        data = b"some file content here"
        assert compute_checksum(data) == compute_checksum(data)

    def test_different_inputs_different_checksums(self):
        assert compute_checksum(b"file1") != compute_checksum(b"file2")
