"""Document text extraction — PDF, DOCX, TXT."""

from __future__ import annotations

import hashlib
import io
import re

import structlog

from app.core.errors import EmptyPdfTextError, PdfTextExtractionFailedError

logger = structlog.get_logger()

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}
SUPPORTED_MIMES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# Magic bytes for file type validation
MAGIC_BYTES = {
    b"%PDF": "application/pdf",
    b"PK": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_file(
    filename: str,
    content: bytes,
    declared_mime: str | None,
    max_size_bytes: int,
) -> tuple[bool, str | None]:
    """Validate uploaded file. Returns (is_valid, error_message)."""
    # Size check
    if len(content) > max_size_bytes:
        return False, f"File exceeds maximum size of {max_size_bytes // (1024*1024)}MB."

    if len(content) == 0:
        return False, "File is empty."

    # Extension check
    ext = _get_extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"

    # Magic bytes check for binary files
    if ext == ".pdf" and not content[:4].startswith(b"%PDF"):
        return False, "File does not appear to be a valid PDF."

    if ext in (".docx",) and not content[:2].startswith(b"PK"):
        return False, "File does not appear to be a valid DOCX document."

    return True, None


def extract_text(filename: str, content: bytes) -> str:
    """Extract text from supported file types."""
    ext = _get_extension(filename)

    if ext == ".txt":
        return _extract_txt(content)
    elif ext == ".pdf":
        return _extract_pdf(content)
    elif ext in (".docx", ".doc"):
        return _extract_docx(content)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_txt(content: bytes) -> str:
    """Extract text from plain text file."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _extract_pdf(content: bytes) -> str:
    """Extract text from PDF across all pages."""
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        text = "\n".join(text_parts)
        if not text.strip():
            logger.warning("pdf_no_text_extracted", hint="May be a scanned PDF requiring OCR")
            raise EmptyPdfTextError("PDF text extraction returned no text.")
        return text
    except EmptyPdfTextError:
        raise
    except Exception as e:
        logger.error("pdf_extraction_failed", error=str(e))
        raise PdfTextExtractionFailedError(f"Failed to extract text from PDF: {e}")


def _extract_docx(content: bytes) -> str:
    """Extract text from DOCX."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error("docx_extraction_failed", error=str(e))
        raise ValueError(f"Failed to extract text from DOCX: {e}")


def clean_text(text: str) -> str:
    """Basic text cleaning while preserving structure."""
    # Replace multiple spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3+ newlines with 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compute_content_hash(text: str) -> str:
    """SHA-256 hash of content for idempotency checks."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Remove path components and dangerous characters from filename."""
    import os
    name = os.path.basename(filename)
    # Remove non-alphanumeric except dots, hyphens, underscores
    name = re.sub(r"[^\w.\-]", "_", name)
    return name[:200]


def _get_extension(filename: str) -> str:
    import os
    return os.path.splitext(filename.lower())[1]
