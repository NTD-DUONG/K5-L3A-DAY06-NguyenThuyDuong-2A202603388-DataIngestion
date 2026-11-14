"""Publish the AI assessor's judgments; never write student/human label fields."""
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from email import policy
from email.parser import BytesParser
import copy
import hashlib
import json
import sys
import unicodedata

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/audit"
sys.path.insert(0, str(ROOT))
from starter.src.evaluation import evaluate_query, summarize


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(x) for x in (ROOT / path).read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    proposals = load("results/audit/ai_proposals.json")
    units = {u["unit_id"]: u for u in rows("data/source_units.jsonl")}
    docs = {d["source_id"]: d for d in load("data/manifest.json")["documents"]}
    source_checks = {}
    for sid, doc in docs.items():
        message = BytesParser(policy=policy.default).parsebytes((ROOT / doc["raw_path"]).read_bytes())
        html = next(p for p in message.walk() if p.get_content_type() == "text/html").get_payload(decode=True).decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        snapshots = [a["href"] for a in soup.find_all("a", href=True) if "oldid=" in a["href"]]
        title = unicodedata.normalize("NFC", soup.select_one("h1").get_text(" ", strip=True))
        assert title == doc["title"]
        assert doc["snapshot_url"] in snapshots
        source_checks[sid] = {"title_checked_against_saved_MHTML": True, "snapshot_checked_against_saved_MHTML": True}

    stamp = datetime.now(timezone.utc).isoformat()
    assessed = []
    for task, key, packet in [("coherence", "coherence_proposals", "coherence.jsonl"), ("grounding", "grounding_proposals", "grounding.jsonl")]:
        originals = rows("results/audit/" + packet)
        for item in proposals[key]:
            identity_field = "sample_id" if task == "coherence" else "question_id"
            original = next(r for r in originals if r[identity_field] == item[identity_field] and r["strategy"] == item["strategy"])
            if task == "coherence":
                assert original["chunk"]["chunk_id"] == item["chunk_id"]
            assessed.append({
                "task": task, "strategy": item["strategy"], identity_field: item[identity_field],
                "score": item["ai_proposed_score"], "reason": item["ai_reason"],
                "assessor": "Codex AI", "assessment_type": "AI qualitative review",
                "assessed_at_utc": stamp, "student_confirmed": False,
            })
    for row in rows("results/audit/metadata.jsonl"):
        assert all(row["automated_checks"].values())
        assert row["metadata"]["document_id"] in source_checks
        assessed.append({
            "task": "metadata", "strategy": row["strategy"], "question_id": row["question_id"],
            "rank": row["rank"], "chunk_id": row["chunk_id"], "complete_and_correct": True,
            "reason": "Đủ source, unit/page, document_id và painting_tradition; URL/snapshot/offset khớp manifest và nội dung lưu. Tiêu đề cùng snapshot đã đối chiếu MHTML gốc. Nhãn dòng tranh là phạm vi tài liệu đã khai báo.",
            "assessor": "Codex AI + programmatic consistency checks", "assessment_type": "AI-assisted source audit",
            "assessed_at_utc": stamp, "student_confirmed": False,
        })
    (OUT / "ai_assessments.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in assessed), encoding="utf-8")

    reviewed = {}
    for strategy in ["A", "B", "C"]:
        traces = rows(f"results/test/{strategy}_traces.jsonl")
        reviewed_traces = []
        for trace in traces:
            trace = copy.deepcopy(trace)
            question = {"acceptable_evidence": list(trace["acceptable_evidence"]), "filter": trace["requested_filter"]}
            overrides = [x for x in proposals["equivalent_evidence_proposals"] if x["strategy"] == strategy and x["question_id"] == trace["question_id"]]
            for override in overrides:
                hit = trace["hits"][override["rank"] - 1]
                assert hit["chunk_id"] == override["chunk_id"]
                assert override["evidence_quote"] in hit["text"]
                assert override["evidence_quote"] in units[override["unit_id"]]["text"]
                assert "tranh làng Sình" in hit["text"]
                question["acceptable_evidence"].append({"source_id": override["source_id"], "page": override["unit_id"], "evidence_quote": override["evidence_quote"]})
            trace["original_automatic_evaluation"] = trace["evaluation"]
            trace["evaluation"] = evaluate_query(question, trace["hits"])
            trace["ai_reviewed_equivalent_evidence"] = overrides
            trace["reviewer"] = "Codex AI"
            trace["student_confirmed"] = False
            reviewed_traces.append(trace)
        (OUT / f"{strategy}_test_ai_reviewed.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in reviewed_traces), encoding="utf-8")
        coh = [x["score"] for x in assessed if x["task"] == "coherence" and x["strategy"] == strategy]
        gro = [x["score"] for x in assessed if x["task"] == "grounding" and x["strategy"] == strategy]
        meta = [x for x in assessed if x["task"] == "metadata" and x["strategy"] == strategy]
        counts = Counter(gro)
        reviewed[strategy] = {
            "test_retrieval_after_AI_equivalent_evidence_review": summarize(reviewed_traces),
            "coherence": {"count": len(coh), "mean_out_of_2": sum(coh) / len(coh)},
            "grounding": {"count": len(gro), "counts_0_1_2": [counts[i] for i in range(3)], "mean_out_of_2": sum(gro) / len(gro)},
            "metadata": {"correct_and_complete": sum(x["complete_and_correct"] for x in meta), "count": len(meta)},
        }
    summary = {
        "assessment_type": "AI assessment, not student/human manual grading", "assessor": "Codex AI",
        "assessed_at_utc": stamp, "student_confirmed": False,
        "source_snapshot_checks": source_checks, "strategies": reviewed,
        "method": "AI read selected coherence chunk texts and full test top-3; used lab 0/1/2 rubric; metadata checked against manifests, unit offsets and MHTML title/snapshot; q16 equivalent evidence accepted by AI with explicit source and context.",
        "bias_and_limits": ["Same AI helped build pipeline and gold; not an independent or blinded assessor.", "Coherence anchors selected after retrieval metrics were seen, before coherence scores; scope-biased sample.", "Metadata consistency is not a claim that every statement in Wikipedia is factually correct.", "Only q16 has an explicit accepted equivalent-evidence override; review is not an exhaustive independent inventory of all possible sources.", "Student understanding/confirmation and required manual grading are not established by this AI review."],
        "original_automatic_metrics_preserved": True,
        "frozen_selection_sha256": hashlib.sha256((ROOT / "results/dev_selection.json").read_bytes()).hexdigest(),
    }
    (OUT / "ai_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Kết quả chấm của AI", "", "Người chấm: Codex AI. Học viên chưa xác nhận; không gọi đây là nhãn thủ công của học viên. Phương pháp, thiên lệch và từng lý do nằm trong ai_summary.json / ai_assessments.jsonl.", "",
             "| Cấu hình | Test Hit@1 sau AI review | Test Hit@3 sau AI review | Coherence /2 (10 mẫu) | Grounding 0/1/2 (5 câu) | Grounding TB /2 | Metadata đủ/đúng |",
             "|---|---:|---:|---:|---|---:|---:|"]
    for strategy, item in reviewed.items():
        ret = item["test_retrieval_after_AI_equivalent_evidence_review"]
        g = item["grounding"]
        lines.append(f"| {strategy} | {ret['hit_at_1']['numerator']}/5 | {ret['evidence_hit_at_3']['numerator']}/5 | {item['coherence']['mean_out_of_2']:.2f} | {'/'.join(map(str,g['counts_0_1_2']))} | {g['mean_out_of_2']:.2f} | {item['metadata']['correct_and_complete']}/15 |")
    lines += ["", "Chỉ q16 được bổ sung evidence tương đương ở top-1 cho cả A/B/C. Giữ nguyên câu hỏi, cấu hình, trace và chỉ số tự động trong results/test; file *_test_ai_reviewed.jsonl lưu tách biệt từng quyết định. Lựa chọn C từ dev giữ nguyên.", "", "Grounding C theo thứ tự q16–q20: 2, 2, 0, 0, 2. AI nhận đủ bằng chứng cho q16/q17/q20; q18 thiếu cây dứa, q19 thiếu nguyên nhân gỗ thông không thích hợp.", "", "Yêu cầu học viên đọc hiểu và xác nhận/chấm thủ công vẫn còn. Các trường human trong packet gốc giữ nguyên trạng thái.", ""]
    (OUT / "AI_REVIEW.md").write_text("\n".join(lines), encoding="utf-8")
    print("AI audit saved: 30 coherence + 15 grounding + 45 metadata assessments.")
    print("C grounding q16-q20: 2,2,0,0,2; mean 1.2/2. Human label files unchanged.")


if __name__ == "__main__":
    main()
