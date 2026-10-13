import io

import pytest
from docx import Document

from app.services.cv_parser import CVParseError, extract_text


def test_docx_text_is_extracted():
    doc = Document()
    doc.add_paragraph("Jeanette Kgabe - Python and SQL developer with React projects")
    buf = io.BytesIO()
    doc.save(buf)
    assert "Python" in extract_text("cv.docx", buf.getvalue())


def test_txt_is_extracted():
    assert "FastAPI" in extract_text("cv.txt", b"Built a FastAPI service with PostgreSQL and Docker")


def test_unsupported_type_is_rejected():
    with pytest.raises(CVParseError):
        extract_text("virus.exe", b"MZ....")


def test_empty_text_is_rejected():
    with pytest.raises(CVParseError):
        extract_text("cv.txt", b"   ")
