"""Unit tests for document service."""

import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from app.services.document import DocumentService


class TestGeneratePdfPreviews:
    def test_returns_jpeg_bytes_per_page(self):
        from PIL import Image

        pages = []
        for _ in range(3):
            img = Image.new("RGB", (100, 100), color="white")
            pages.append(img)

        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_bytes = MagicMock(return_value=pages)
        with patch.dict("sys.modules", {"pdf2image": mock_pdf2image}):
            result = DocumentService.generate_pdf_previews(b"fake-pdf-data", max_pages=3)

        assert len(result) == 3
        for page_bytes in result:
            assert isinstance(page_bytes, bytes)
            assert len(page_bytes) > 0
            img = Image.open(BytesIO(page_bytes))
            assert img.format == "JPEG"

    def test_respects_max_pages(self):
        mock_convert = MagicMock(return_value=[])
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_bytes = mock_convert
        with patch.dict("sys.modules", {"pdf2image": mock_pdf2image}):
            DocumentService.generate_pdf_previews(b"data", max_pages=5)

        _, kwargs = mock_convert.call_args
        assert kwargs["last_page"] == 5

    def test_returns_empty_on_error(self):
        result = DocumentService.generate_pdf_previews(b"not-a-pdf")
        assert result == []


class TestConvertOfficeToPdf:
    @patch("app.services.document.subprocess.run")
    def test_calls_libreoffice_headless(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)

        DocumentService.convert_office_to_pdf(b"fake-docx", "test.docx")

        args = mock_run.call_args[0][0]
        assert "libreoffice" in args
        assert "--headless" in args
        assert "--convert-to" in args
        assert "pdf" in args

    @patch("app.services.document.subprocess.run")
    def test_returns_none_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)

        result = DocumentService.convert_office_to_pdf(b"data", "test.docx")
        assert result is None

    @patch("app.services.document.os.path.exists", return_value=True)
    @patch("builtins.open", create=True)
    @patch("app.services.document.subprocess.run")
    @patch("app.services.document.tempfile.TemporaryDirectory")
    def test_returns_pdf_bytes_on_success(self, mock_tmpdir, mock_run, mock_open_fn, mock_exists):
        mock_tmpdir.return_value.__enter__ = MagicMock(return_value="/tmp/fakedir")
        mock_tmpdir.return_value.__exit__ = MagicMock(return_value=False)
        mock_run.return_value = MagicMock(returncode=0)

        fake_pdf = b"%PDF-1.4 fake pdf content"
        mock_file = MagicMock()
        mock_file.read.return_value = fake_pdf
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_open_fn.return_value = mock_file

        result = DocumentService.convert_office_to_pdf(b"docx-data", "report.docx")
        assert result == fake_pdf


class TestExtractTextFromPdf:
    def test_extracts_text(self):
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello World"

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = DocumentService.extract_text_from_pdf(b"fake-pdf")

        assert result == "Hello World"
        mock_doc.close.assert_called_once()

    def test_concatenates_pages(self):
        pages = []
        for text in ["Page 1", "Page 2", "Page 3"]:
            p = MagicMock()
            p.get_text.return_value = text
            pages.append(p)

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter(pages))

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = DocumentService.extract_text_from_pdf(b"pdf-data")

        assert "Page 1" in result
        assert "Page 2" in result
        assert "Page 3" in result

    def test_returns_empty_on_error(self):
        result = DocumentService.extract_text_from_pdf(b"not-a-pdf")
        assert result == ""
