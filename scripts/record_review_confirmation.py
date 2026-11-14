"""Record the student's explicit confirmation of the assisted review packet."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/audit"


def main():
    confirmation_path = OUT / "student_confirmation.json"
    if confirmation_path.exists():
        raise RuntimeError("Confirmation already recorded; do not overwrite the audit trail")
    assessor = "Nguyễn Thùy Dương"
    stamp = datetime.now(timezone.utc).isoformat()
    source = OUT / "ai_assessments.jsonl"
    assessments = [json.loads(x) for x in source.read_text(encoding="utf-8").splitlines() if x.strip()]
    for task, field in [("coherence", "human_score"), ("grounding", "human_score"), ("metadata", "human_complete_and_correct")]:
        path = OUT / f"{task}.jsonl"
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        for row in rows:
            keys = ["strategy", "sample_id"] if task == "coherence" else ["strategy", "question_id"]
            if task == "metadata":
                keys += ["rank", "chunk_id"]
            decision = next(x for x in assessments if x["task"] == task and all(x[k] == row[k] for k in keys))
            if row[field] is not None:
                raise RuntimeError("Existing student label requires separate review, not replacement")
            row[field] = decision["complete_and_correct"] if task == "metadata" else decision["score"]
            row["human_reason"] = decision["reason"]
            row["reviewer"] = assessor
            row["reviewed_at_utc"] = stamp
            row["confirmation_method"] = "Học viên xác nhận toàn bộ phiếu chấm đã được trợ lý hỗ trợ soạn qua hội thoại."
            row["label_origin"] = "Assisted draft, explicitly confirmed by student; not independent/blinded grading"
        path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")

    proposals = json.loads((OUT / "ai_proposals.json").read_text(encoding="utf-8"))
    equivalent = []
    for item in proposals["equivalent_evidence_proposals"]:
        item = dict(item)
        item["human_confirmed"] = True
        item["reviewer"] = assessor
        item["reviewed_at_utc"] = stamp
        equivalent.append(item)
    (OUT / "confirmed_equivalent_evidence.json").write_text(json.dumps(equivalent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    reviewed = OUT / "confirmed_test"
    reviewed.mkdir(exist_ok=True)
    metrics = {}
    from starter.src.evaluation import summarize
    for strategy in ["A", "B", "C"]:
        path = OUT / f"{strategy}_test_ai_reviewed.jsonl"
        traces = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        for trace in traces:
            trace["reviewer"] = assessor
            trace["student_confirmed"] = True
            trace["confirmation_method"] = "Student confirmed the assisted evidence review in conversation"
        (reviewed / f"{strategy}_traces.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in traces), encoding="utf-8")
        metrics[strategy] = summarize(traces)
    (reviewed / "summary.json").write_text(json.dumps({
        "reviewer": assessor, "student_confirmed": True, "confirmed_at_utc": stamp,
        "method": "Assisted qualitative review explicitly confirmed by student; q16 equivalent evidence accepted; original automatic results preserved",
        "strategies": metrics,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    confirmation_path.write_text(json.dumps({
        "reviewer": assessor, "confirmed_at_utc": stamp,
        "user_statement": "ok tôi xác nhận rồi",
        "scope": "30 coherence labels, 15 grounding labels, 45 metadata labels, and q16 equivalent evidence in the presented review packet",
        "confirmation_type": "Adoption/confirmation of assisted judgments; not a claim of independent blind grading",
        "source_assessments_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_manual_reading_sheet_sha256": hashlib.sha256((OUT / "CHAM_DOC_TUNG_MAU.md").read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Recorded explicit student confirmation for 90 audit records and equivalent evidence. Baseline metrics unchanged.")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    main()
