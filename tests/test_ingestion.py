from pathlib import Path

import pytest

from verinli.ingestion import load_evidence_file, passages_from_jsonl, passages_from_text


def test_plain_text_paragraphs_become_passages() -> None:
    passages = passages_from_text("First paragraph.\n\nSecond paragraph.", source="notes.md")
    assert [item.passage_id for item in passages] == ["text-001", "text-002"]
    assert all(item.source == "notes.md" for item in passages)


def test_long_plain_text_is_split_at_sentence_boundaries() -> None:
    text = "First sentence has useful evidence. Second sentence adds more detail."
    passages = passages_from_text(text, max_characters=100)
    assert " ".join(item.text for item in passages) == text


def test_jsonl_reports_the_invalid_line() -> None:
    with pytest.raises(ValueError, match="line 2"):
        passages_from_jsonl('{"passage_id":"a","text":"valid"}\nnot-json')


def test_load_plain_text_file(tmp_path: Path) -> None:
    evidence_file = tmp_path / "evidence.txt"
    evidence_file.write_text("Local evidence text.", encoding="utf-8")
    passages = load_evidence_file(evidence_file)
    assert passages[0].source == "evidence.txt"
