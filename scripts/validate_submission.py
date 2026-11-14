"""Read-only checks for existing lab artifacts; report remaining human work."""
from pathlib import Path
import hashlib
import json
import sys
from email import policy
from email.parser import BytesParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from starter.src.evaluation import evaluate_query, summarize


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(x) for x in (ROOT / path).read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    manifest = load("data/manifest.json")
    units = lines("data/source_units.jsonl")
    by_id = {u["unit_id"]: u for u in units}
    assert len(by_id) == len(units) >= 30
    assert all(u["char_count"] == len(u["text"]) >= 1500 for u in units)
    assert {uid for d in manifest["documents"] for uid in d["unit_ids"]} == set(by_id)
    for doc in manifest["documents"]:
        assert (ROOT / doc["raw_path"]).is_file()
        message = BytesParser(policy=policy.default).parsebytes((ROOT / doc["raw_path"]).read_bytes())
        assert [part.get_content_type() for part in message.walk() if not part.is_multipart()] == ["text/html"]
        text = (ROOT / doc["processed_path"]).read_text(encoding="utf-8")
        assert len(text) == doc["char_count"]
        for uid in doc["unit_ids"]:
            unit = by_id[uid]
            assert text[unit["start_char"]:unit["end_char"]] == unit["text"]
    questions = load("benchmark/questions.json")
    assert len(questions) >= 20
    assert sum(q["split"] == "dev" for q in questions) == 15
    assert sum(q["split"] == "test" for q in questions) == 5
    assert sum(bool(q["filter"]) for q in questions) >= 3
    assert any(q["filter"] and q["split"] == "test" for q in questions)
    for q in questions:
        assert q["evidence_quote"] in by_id[q["gold_page"]]["text"]
    assert lines("artifacts/chunks/B.jsonl") == lines("artifacts/chunks/C.jsonl")
    frozen = load("results/dev_selection.json")
    for split in ["dev", "test"]:
        summary = load(f"results/{split}/summary.json")
        for strategy in ["A", "B", "C"]:
            traces = lines(f"results/{split}/{strategy}_traces.jsonl")
            assert len(traces) == (15 if split == "dev" else 5)
            for trace in traces:
                q = next(q for q in questions if q["id"] == trace["question_id"])
                assert q["split"] == split and len(trace["hits"]) == 3
                assert evaluate_query(q, trace["hits"]) == trace["evaluation"]
                for hit in trace["hits"]:
                    meta = hit["metadata"]
                    unit = by_id[meta["page"]]
                    assert hit["text"] == unit["text"][meta["unit_start_offset"]:meta["unit_end_offset"]]
            assert summarize(traces) == summary["strategies"][strategy]
    assert load("results/test/summary.json")["frozen_selection_sha256"] == hashlib.sha256((ROOT / "results/dev_selection.json").read_bytes()).hexdigest()
    assert frozen["test_retrieval_executed_at_selection"] is False
    print("PASS: 7 sources / 30 units / 20 questions / 60 traces / matching metrics and frozen selection")
    pending = {}
    for name, field in [("coherence", "human_score"), ("grounding", "human_score"), ("metadata", "human_complete_and_correct")]:
        rows = lines(f"results/audit/{name}.jsonl")
        pending[name] = sum(row[field] is None or not row.get("reviewer") or not row.get("human_reason") for row in rows)
    assert all(count == 0 for count in pending.values()), pending
    report = ROOT / "report/individual/2A202603388_NguyenThuyDuong.md"
    assert report.is_file()
    student = (ROOT / "STUDENT.md").read_text(encoding="utf-8")
    assert "2A202603388" in student and "L3A" in student and "Nguyễn Thùy Dương" in student
    assert "https://github.com/NTD-DUONG/K5-L3A-DAY06-NguyenThuyDuong-2A202603388-DataIngestion" in student
    assert "refs/tags/submission-day06-v4" in student
    print("PASS: complete confirmed audit labels, text-only source packages, student information and final report")
    print("Repository publication and course submission are checked separately.")


if __name__ == "__main__":
    main()
