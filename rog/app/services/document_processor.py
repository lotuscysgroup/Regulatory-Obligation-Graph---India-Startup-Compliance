from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import docx
import pdfplumber
from sqlalchemy.orm import Session

from rog.app.models.section import Section

logger = logging.getLogger(__name__)

_SECTION_RE = re.compile(
    r"^\s*(?P<number>(?:\d+(?:\.\d+){0,5}|Article\s+\d+|Clause\s+\d+))"
    r"(?:[\)\].:-]?\s*(?P<title>.*))?\s*$",
    re.IGNORECASE,
)


@dataclass(slots=True)
class SectionCandidate:
    section_number: str | None
    title: str | None
    content: str
    order_index: int


def extract_text_from_pdf(file_path: str) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


def clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    lines = [ln.strip() for ln in normalized.split("\n")]
    # Keep paragraph boundaries while removing accidental empty streaks.
    return "\n".join(lines).strip()


def detect_sections(text: str) -> list[SectionCandidate]:
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines:
        return []

    starts: list[tuple[int, str | None, str | None]] = []
    for idx, line in enumerate(lines):
        match = _SECTION_RE.match(line)
        if not match:
            continue
        number = match.group("number")
        title = (match.group("title") or "").strip() or None
        starts.append((idx, number, title))

    if not starts:
        return [SectionCandidate(section_number=None, title="Full Document", content="\n".join(lines), order_index=1)]

    candidates: list[SectionCandidate] = []
    for order, (start_idx, number, title) in enumerate(starts, start=1):
        end_idx = starts[order][0] if order < len(starts) else len(lines)
        body_lines = lines[start_idx + 1 : end_idx]
        # If first line has extra title text and no body lines, keep title as content fallback.
        body = "\n".join(body_lines).strip()
        if not body and title:
            body = title
        candidates.append(SectionCandidate(section_number=number, title=title, content=body, order_index=order))

    return candidates


def _parent_number(section_number: str | None) -> str | None:
    if not section_number:
        return None
    s = section_number.strip()
    lower = s.lower()
    if lower.startswith("article ") or lower.startswith("clause "):
        return None
    if "." in s:
        return s.rsplit(".", 1)[0]
    return None


class DocumentProcessor:
    def __init__(self, db: Session) -> None:
        self.db = db

    def process_and_store(self, *, regulation_version_id: uuid.UUID, file_path: str, file_type: str) -> int:
        logger.info(
            "extraction_start regulation_version_id=%s file_type=%s file_path=%s",
            regulation_version_id,
            file_type,
            file_path,
        )
        try:
            if file_type == "pdf":
                raw_text = extract_text_from_pdf(file_path)
            elif file_type == "docx":
                raw_text = extract_text_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file_type: {file_type}")

            cleaned = clean_text(raw_text)
            candidates = detect_sections(cleaned)

            number_to_id: dict[str, uuid.UUID] = {}
            created = 0
            for c in candidates:
                parent_id = None
                parent_num = _parent_number(c.section_number)
                if parent_num:
                    parent_id = number_to_id.get(parent_num)

                section = Section(
                    regulation_version_id=regulation_version_id,
                    section_number=c.section_number,
                    title=c.title,
                    content=c.content or "",
                    parent_section_id=parent_id,
                    order_index=c.order_index,
                )
                self.db.add(section)
                self.db.flush()
                created += 1
                if c.section_number:
                    number_to_id[c.section_number] = section.id

            self.db.commit()
            logger.info(
                "extraction_success regulation_version_id=%s sections_created=%s",
                regulation_version_id,
                created,
            )
            return created
        except Exception:
            self.db.rollback()
            logger.exception("extraction_error regulation_version_id=%s", regulation_version_id)
            raise

