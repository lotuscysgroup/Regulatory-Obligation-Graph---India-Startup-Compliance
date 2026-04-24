from __future__ import annotations

from types import SimpleNamespace

from rog.app.services.document_processor import (
    clean_text,
    detect_sections,
    extract_text_from_docx,
    extract_text_from_pdf,
)


def test_pdf_extraction(monkeypatch) -> None:
    class FakePDF:
        def __enter__(self):
            self.pages = [SimpleNamespace(extract_text=lambda: "Page 1"), SimpleNamespace(extract_text=lambda: "Page 2")]
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("rog.app.services.document_processor.pdfplumber.open", lambda _path: FakePDF())
    text = extract_text_from_pdf("dummy.pdf")
    assert text == "Page 1\nPage 2"


def test_docx_extraction(monkeypatch) -> None:
    fake_doc = SimpleNamespace(paragraphs=[SimpleNamespace(text="Para 1"), SimpleNamespace(text="Para 2")])
    monkeypatch.setattr("rog.app.services.document_processor.docx.Document", lambda _path: fake_doc)
    text = extract_text_from_docx("dummy.docx")
    assert text == "Para 1\nPara 2"


def test_section_detection() -> None:
    raw = """
    1 Introduction
    Intro content.
    1.1 Scope
    Scope content.
    Article 2 Definitions
    Definitions content.
    Clause 5 Penalty
    Penalty content.
    """
    cleaned = clean_text(raw)
    sections = detect_sections(cleaned)
    assert len(sections) == 4
    assert sections[0].section_number == "1"
    assert sections[1].section_number == "1.1"
    assert sections[2].section_number.lower() == "article 2"
    assert sections[3].section_number.lower() == "clause 5"

