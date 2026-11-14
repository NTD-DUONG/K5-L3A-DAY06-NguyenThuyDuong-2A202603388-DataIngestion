"""Prepare reproducible review packets; never invent student/human labels."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_lines(path, rows):
    if path.exists():
        raise RuntimeError(f"Review packet already exists; do not overwrite annotations: {path}")
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def main():
    out = ROOT / "results/audit"
    out.mkdir(parents=True, exist_ok=True)
    units = {u["unit_id"]: u for u in read_lines(ROOT / "data/source_units.jsonl")}
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    docs = {d["source_id"]: d for d in manifest["documents"]}
    scopes = json.loads((ROOT / "benchmark/metadata_scopes.json").read_text(encoding="utf-8"))["document_values"]
    chunks = {s: read_lines(ROOT / f"artifacts/chunks/{s}.jsonl") for s in ["A", "B", "C"]}
    anchors = []
    for uid in sorted(units)[:10]:
        text = units[uid]["text"]
        anchor = 750
        while text[anchor].isspace():
            anchor += 1
        anchors.append({"unit_id": uid, "unit_offset": anchor})
    protocol = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "coherence_sampling": "First 10 unit IDs sorted lexicographically; anchor at character 750, move right over whitespace. If multiple chunks contain anchor, choose smallest unit_start_offset, then chunk_id.",
        "anchors": anchors,
        "sampling_limitations": "Sampling rule recorded after retrieval metrics were seen, before coherence labels. First units overrepresent paper/general sources; not a random representative sample.",
        "coherence_scale": {"0": "Cắt giữa ý/thiếu chủ thể khiến không hiểu", "1": "Hiểu một phần, thiếu ngữ cảnh", "2": "Tự hiểu được, giữ trọn ý"},
        "grounding_scale": {"0": "Không có bằng chứng trả lời", "1": "Có nhưng thiếu điều kiện/ngữ cảnh", "2": "Đủ bằng chứng trả lời và truy nguồn"},
        "human_labels": "Must be filled by student after reading. AI proposals remain separate and are not human labels.",
    }
    protocol_path = out / "protocol.json"
    if protocol_path.exists():
        raise RuntimeError("Audit sampling protocol already exists")
    protocol_path.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    coherence = []
    for sample_id, anchor in enumerate(anchors, 1):
        uid, offset = anchor["unit_id"], anchor["unit_offset"]
        for strategy in ["A", "B", "C"]:
            matches = [c for c in chunks[strategy] if c["page"] == uid and c["metadata"]["unit_start_offset"] <= offset < c["metadata"]["unit_end_offset"]]
            chosen = min(matches, key=lambda c: (c["metadata"]["unit_start_offset"], c["chunk_id"]))
            coherence.append({
                "sample_id": f"coh{sample_id:02d}", "strategy": strategy,
                "unit_id": uid, "anchor_offset": offset,
                "source_context": units[uid]["text"][max(0, offset - 250):offset + 250],
                "chunk": chosen, "human_score": None, "human_reason": "", "reviewer": "",
            })
    write_lines(out / "coherence.jsonl", coherence)

    grounding, metadata, equivalent = [], [], []
    for strategy in ["A", "B", "C"]:
        traces = read_lines(ROOT / f"results/test/{strategy}_traces.jsonl")
        for trace in traces:
            grounding.append({
                "strategy": strategy, "question_id": trace["question_id"],
                "question": trace["question"], "expected_answer": trace["expected_answer"],
                "gold_quote": trace["evidence_quote"], "hits": trace["hits"],
                "human_score": None, "human_reason": "", "reviewer": "",
            })
            for rank, hit in enumerate(trace["hits"], 1):
                meta = hit["metadata"]
                doc = docs[meta["document_id"]]
                unit = units[meta["page"]]
                source_text = (ROOT / doc["processed_path"]).read_text(encoding="utf-8")
                checks = {
                    "document_and_unit_match": unit["document_id"] == doc["source_id"],
                    "source_url_matches_manifest": meta["source"] == doc["source_path_or_url"],
                    "snapshot_matches_manifest": meta["snapshot_url"] == doc["snapshot_url"],
                    "tradition_matches_declared_scope": meta["painting_tradition"] == scopes[doc["source_id"]],
                    "text_matches_source_offsets": hit["text"] == source_text[meta["document_start_char"]:meta["document_end_char"]],
                }
                metadata.append({
                    "strategy": strategy, "question_id": trace["question_id"], "rank": rank,
                    "chunk_id": hit["chunk_id"], "metadata": meta, "text": hit["text"],
                    "source_reference": {"title": doc["title"], "snapshot_url": doc["snapshot_url"], "unit_id": unit["unit_id"]},
                    "automated_checks": checks,
                    "filter_requested": trace["requested_filter"],
                    "filter_obeyed": all(meta.get(k) == v for k, v in trace["requested_filter"].items()) if trace["requested_filter"] else None,
                    "human_complete_and_correct": None, "human_reason": "", "reviewer": "",
                })
    write_lines(out / "grounding.jsonl", grounding)
    write_lines(out / "metadata.jsonl", metadata)

    check_summary = {s: {
        "checked_records": sum(row["strategy"] == s for row in metadata),
        "records_passing_automated_consistency_checks": sum(row["strategy"] == s and all(row["automated_checks"].values()) for row in metadata),
        "human_reviewed_records": 0,
    } for s in ["A", "B", "C"]}
    (out / "automated_metadata_checks.json").write_text(json.dumps(check_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Prepared 30 coherence rows, 15 grounding rows, 45 metadata rows; all human labels blank.")


if __name__ == "__main__":
    main()
