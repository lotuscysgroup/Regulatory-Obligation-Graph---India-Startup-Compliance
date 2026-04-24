from rog.app.services.obligation_extractor import (
    detect_deadline_text,
    detect_penalty_text,
    extract_obligations_from_text,
)


def test_mandatory_clause_detection() -> None:
    text = "The company shall maintain statutory records."
    obligations = extract_obligations_from_text(text)
    assert len(obligations) == 1
    assert obligations[0].mandatory_flag is True
    assert obligations[0].responsible_party == "company"


def test_deadline_detection() -> None:
    text = "The employer must submit returns within 30 days."
    deadline = detect_deadline_text(text)
    assert deadline is not None
    assert deadline.lower() == "within 30 days"


def test_penalty_detection() -> None:
    text = "Any default is punishable with fine up to INR 1,00,000."
    penalty = detect_penalty_text(text)
    assert penalty is not None
    assert "punishable" in penalty.lower()

