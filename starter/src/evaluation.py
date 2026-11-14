"""Automatic evidence matching; human grounding/coherence remain separate."""
from typing import Any
import unicodedata


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Require a valid gold source/unit AND the complete evidence in one chunk."""
    golds = question.get("acceptable_evidence") or [{
        "source_id": question["gold_source_id"], "page": question["gold_page"],
        "evidence_quote": question["evidence_quote"],
    }]
    matches = []
    for hit in hits[:3]:
        metadata = hit["metadata"]
        matches.append(any(
            metadata["document_id"] == gold["source_id"]
            and metadata["page"] == gold["page"]
            and bool(_normalize(gold["evidence_quote"]))
            and _normalize(gold["evidence_quote"]) in _normalize(hit["text"])
            for gold in golds
        ))
    requested = question.get("filter")
    obeys = all(all(hit["metadata"].get(key) == value for key, value in requested.items()) for hit in hits[:3]) if requested and hits else None
    return {
        "hit_at_1": bool(matches and matches[0]),
        "evidence_hit_at_3": any(matches), "rank_evidence_matches": matches,
        "requested_filter_top3_compliance": obeys,
        "evaluation_method": "Automatic full evidence substring after Unicode/whitespace normalization, plus gold source and unit. Equivalent evidence without an exact match requires later review.",
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize one strategy and one split, with explicit numerators."""
    if not traces or len({(row["strategy"], row["split"]) for row in traces}) != 1:
        raise ValueError("Require nonempty traces from exactly one strategy/split")
    n = len(traces)
    hit1 = sum(row["evaluation"]["hit_at_1"] for row in traces)
    hit3 = sum(row["evaluation"]["evidence_hit_at_3"] for row in traces)
    filters = [row for row in traces if row["requested_filter"]]
    compliant = sum(row["evaluation"]["requested_filter_top3_compliance"] is True for row in filters)
    return {
        "strategy": traces[0]["strategy"], "split": traces[0]["split"],
        "question_count": n,
        "hit_at_1": {"numerator": hit1, "denominator": n, "value": hit1 / n},
        "evidence_hit_at_3": {"numerator": hit3, "denominator": n, "value": hit3 / n},
        "filter_compliance": {"numerator": compliant, "denominator": len(filters), "value": compliant / len(filters) if filters else None},
        "failed_question_ids": [row["question_id"] for row in traces if not row["evaluation"]["evidence_hit_at_3"]],
    }
