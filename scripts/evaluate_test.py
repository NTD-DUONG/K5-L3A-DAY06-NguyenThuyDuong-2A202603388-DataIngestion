"""Evaluate the held-out split after verifying the frozen dev selection."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from starter.src.embeddings import MyEmbedder
from starter.src.chroma_store import ChromaStore
from starter.src.evaluation import evaluate_query, summarize


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Evaluate test after frozen dev selection")
    parser.add_argument("--results-dir", default="results", help="Run artifacts directory relative to the repo")
    args = parser.parse_args()
    results_dir = (ROOT / args.results_dir).resolve()
    results_dir.relative_to(ROOT)
    selection_path = results_dir / "dev_selection.json"
    frozen = json.loads(selection_path.read_text(encoding="utf-8"))
    frozen_hash = sha(selection_path)
    checks = {
        "questions_sha256": ROOT / "benchmark/questions.json",
        "strategies_config_sha256": ROOT / "configs/strategies.json",
        "source_units_sha256": ROOT / "data/source_units.jsonl",
        "dev_summary_sha256": results_dir / "dev/summary.json",
    }
    for key, path in checks.items():
        if sha(path) != frozen[key]:
            raise ValueError(f"Frozen input changed: {path}")
    assert frozen["test_retrieval_executed_at_selection"] is False
    for strategy, digest in frozen["chunk_hashes"].items():
        assert sha(ROOT / f"artifacts/chunks/{strategy}.jsonl") == digest

    out = results_dir / "test"
    if (out / "summary.json").exists():
        raise RuntimeError("Test already evaluated; inspect stored results rather than overwrite the holdout run")
    protocol = json.loads((ROOT / "benchmark/protocol.json").read_text(encoding="utf-8"))
    questions = [q for q in json.loads(checks["questions_sha256"].read_text(encoding="utf-8")) if q["split"] == "test"]
    assert [q["id"] for q in questions] == protocol["test_ids"]
    configs = json.loads(checks["strategies_config_sha256"].read_text(encoding="utf-8"))
    ingestion = json.loads((results_dir / "ingestion/summary.json").read_text(encoding="utf-8"))
    embedder = MyEmbedder(ingestion["model"]["model_name"])
    signature = hashlib.sha256(json.dumps(embedder.configuration, sort_keys=True).encode()).hexdigest()
    assert signature == frozen["model_signature"] == ingestion["model_signature"]
    store = ChromaStore(ROOT / ingestion["vector_store"]["path"], embedder.dimensions, signature)
    started = time.perf_counter()
    vectors = embedder.embed_documents([q["question"] for q in questions])
    embedding_seconds = time.perf_counter() - started
    out.mkdir(parents=True, exist_ok=True)
    reports = {}
    for strategy in ["A", "B", "C"]:
        assert store.collection(strategy).count() == ingestion["strategies"][strategy]["chunk_count"]
        traces = []
        for question, vector in zip(questions, vectors):
            applied = question["filter"] if configs[strategy]["use_metadata_filter"] else None
            started = time.perf_counter()
            hits = store.search(strategy, vector, top_k=3, filters=applied)
            elapsed = time.perf_counter() - started
            assert len(hits) == 3
            evaluation = evaluate_query(question, hits)
            if applied:
                assert evaluation["requested_filter_top3_compliance"] is True
            traces.append({
                "strategy": strategy, "split": "test", "question_id": question["id"],
                "question": question["question"], "requested_filter": question["filter"],
                "applied_filter": applied, "expected_answer": question["expected_answer"],
                "gold_source_id": question["gold_source_id"], "gold_page": question["gold_page"],
                "evidence_quote": question["evidence_quote"],
                "acceptable_evidence": question["acceptable_evidence"],
                "retrieval_seconds": elapsed, "hits": hits, "evaluation": evaluation,
            })
        (out / f"{strategy}_traces.jsonl").write_text(
            "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in traces), encoding="utf-8")
        reports[strategy] = summarize(traces)
        print(f"{strategy}: Hit@1 {reports[strategy]['hit_at_1']['numerator']}/5; Evidence Hit@3 {reports[strategy]['evidence_hit_at_3']['numerator']}/5")

    assert sha(selection_path) == frozen_hash, "Dev selection must remain unchanged"
    summary = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(), "split": "test",
        "selected_strategy_from_dev": frozen["selected_strategy"],
        "selection_frozen_at_utc": frozen["frozen_at_utc"],
        "frozen_selection_sha256": frozen_hash, "frozen_inputs_verified": True,
        "strategies": reports, "query_embedding_seconds_shared": embedding_seconds,
        "limitations": [
            "Five test questions only; do not infer universal superiority.",
            "Automatic full evidence matches; valid equivalent evidence may need human review.",
            "No human coherence, metadata or grounding labels have been assigned by this script.",
            "Do not tune on these test results and continue calling the same split an independent holdout.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["strategy", "split", "hit_at_1_n", "evidence_hit_at_3_n", "questions", "filter_compliant_n", "filter_questions"])
        for strategy, report in reports.items():
            writer.writerow([strategy, "test", report["hit_at_1"]["numerator"], report["evidence_hit_at_3"]["numerator"], len(questions), report["filter_compliance"]["numerator"], report["filter_compliance"]["denominator"]])
    print(f"Frozen dev choice remains {frozen['selected_strategy']}; no configuration changed.")


if __name__ == "__main__":
    main()
