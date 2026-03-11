import os
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path


class DocumentService:
    @staticmethod
    def generate_pdf_previews(file_data: bytes, max_pages: int = 10) -> list[bytes]:
        """Convert PDF pages to images."""
        try:
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(
                file_data,
                first_page=1,
                last_page=max_pages,
                dpi=150,
                fmt="jpeg",
            )
            result = []
            for img in images:
                buf = BytesIO()
                img.save(buf, format="JPEG", quality=85)
                result.append(buf.getvalue())
            return result
        except Exception:
            return []

    @staticmethod
    def convert_office_to_pdf(
        file_data: bytes, original_filename: str
    ) -> bytes | None:
        """Convert Office document to PDF using LibreOffice headless."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, original_filename)
            with open(input_path, "wb") as f:
                f.write(file_data)

            cmd = [
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", tmpdir, input_path,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)

            if result.returncode != 0:
                return None

            pdf_path = os.path.join(tmpdir, Path(original_filename).stem + ".pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read()
            return None

    @staticmethod
    def generate_office_previews(
        file_data: bytes, original_filename: str, max_pages: int = 10
    ) -> list[bytes]:
        """Convert Office document to preview images via PDF intermediate."""
        pdf_data = DocumentService.convert_office_to_pdf(file_data, original_filename)
        if pdf_data:
            return DocumentService.generate_pdf_previews(pdf_data, max_pages)
        return []

    @staticmethod
    def extract_text_from_pdf(file_data: bytes) -> str:
        """Extract text content from PDF."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=file_data, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
        except Exception:
            return ""
