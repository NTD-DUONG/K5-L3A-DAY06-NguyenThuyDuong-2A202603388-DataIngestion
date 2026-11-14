"""Run dev only, record top-3, and freeze selection before any test retrieval."""
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
    parser = argparse.ArgumentParser(description="Evaluate dev and freeze the selected strategy")
    parser.add_argument("--results-dir", default="results", help="Run artifacts directory relative to the repo")
    args = parser.parse_args()
    results_dir = (ROOT / args.results_dir).resolve()
    results_dir.relative_to(ROOT)
    protocol = json.loads((ROOT / "benchmark/protocol.json").read_text(encoding="utf-8"))
    question_path = ROOT / "benchmark/questions.json"
    # Windows editors may convert LF to CRLF without changing benchmark content.
    question_lf_hash = hashlib.sha256(question_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert question_lf_hash == protocol["questions_sha256"], "Question set differs from protocol"
    assert sha(ROOT / "data/source_units.jsonl") == protocol["source_units_sha256"]
    # Load shared benchmark file, but only dev questions are embedded/searched.
    questions = [q for q in json.loads(question_path.read_text(encoding="utf-8")) if q["split"] == "dev"]
    assert [q["id"] for q in questions] == protocol["dev_ids"]
    ingestion = json.loads((results_dir / "ingestion/summary.json").read_text(encoding="utf-8"))
    configs = json.loads((ROOT / "configs/strategies.json").read_text(encoding="utf-8"))
    frozen_path = results_dir / "dev_selection.json"
    if frozen_path.exists():
        raise RuntimeError("Dev selection is already frozen. Review existing results rather than silently overwriting.")
    embedder = MyEmbedder(ingestion["model"]["model_name"])
    signature = hashlib.sha256(json.dumps(embedder.configuration, sort_keys=True).encode()).hexdigest()
    assert signature == ingestion["model_signature"], "Embedding configuration changed"
    store = ChromaStore(ROOT / ingestion["vector_store"]["path"], embedder.dimensions, signature)
    out = results_dir / "dev"
    out.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    vectors = embedder.embed_documents([q["question"] for q in questions])
    embedding_seconds = time.perf_counter() - started
    reports, trace_paths = {}, {}
    for strategy in ["A", "B", "C"]:
        assert sha(ROOT / f"artifacts/chunks/{strategy}.jsonl") == ingestion["strategies"][strategy]["chunks_sha256"]
        assert store.collection(strategy).count() == ingestion["strategies"][strategy]["chunk_count"]
        traces = []
        for question, vector in zip(questions, vectors):
            applied_filter = question["filter"] if configs[strategy]["use_metadata_filter"] else None
            started = time.perf_counter()
            # Only question text embeddings and supplied filters go to retrieval.
            hits = store.search(strategy, vector, top_k=3, filters=applied_filter)
            elapsed = time.perf_counter() - started
            assert len(hits) == 3
            evaluation = evaluate_query(question, hits)
            if applied_filter:
                assert evaluation["requested_filter_top3_compliance"] is True
            traces.append({
                "strategy": strategy, "split": "dev", "question_id": question["id"],
                "question": question["question"], "requested_filter": question["filter"],
                "applied_filter": applied_filter,
                "expected_answer": question["expected_answer"],
                "gold_source_id": question["gold_source_id"], "gold_page": question["gold_page"],
                "evidence_quote": question["evidence_quote"],
                "acceptable_evidence": question["acceptable_evidence"],
                "retrieval_seconds": elapsed, "hits": hits, "evaluation": evaluation,
            })
        path = out / f"{strategy}_traces.jsonl"
        path.write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in traces), encoding="utf-8")
        trace_paths[strategy] = path.relative_to(ROOT).as_posix()
        reports[strategy] = summarize(traces)
        print(f"{strategy}: Hit@1 {reports[strategy]['hit_at_1']['numerator']}/15; Evidence Hit@3 {reports[strategy]['evidence_hit_at_3']['numerator']}/15")

    summary = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": "dev", "questions_sha256": sha(question_path),
        "strategies": reports, "trace_paths": trace_paths,
        "query_embedding_seconds_shared": embedding_seconds,
        "test_retrieval_executed": False,
        "limitations": ["Automatic exact-evidence matching can miss valid paraphrased/alternative evidence; review traces manually.", "These results do not substitute for human coherence, metadata or grounding labels.", "Small dev set, correlated topics and AI-assisted gold limit generalization."],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["strategy", "split", "hit_at_1_n", "evidence_hit_at_3_n", "questions", "filter_compliant_n", "filter_questions"])
        for strategy, report in reports.items():
            writer.writerow([strategy, "dev", report["hit_at_1"]["numerator"], report["evidence_hit_at_3"]["numerator"], 15, report["filter_compliance"]["numerator"], report["filter_compliance"]["denominator"]])
    selected = min(reports, key=lambda name: (
        -reports[name]["evidence_hit_at_3"]["numerator"],
        -reports[name]["hit_at_1"]["numerator"],
        ingestion["strategies"][name]["chunk_count"], name,
    ))
    frozen_path.write_text(json.dumps({
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "selected_strategy": selected,
        "selection_rule": protocol["selection_rule"], "basis": "automatic dev evidence metrics",
        "questions_sha256": sha(question_path), "strategies_config_sha256": sha(ROOT / "configs/strategies.json"),
        "source_units_sha256": sha(ROOT / "data/source_units.jsonl"),
        "model_signature": signature,
        "chunk_hashes": {name: ingestion["strategies"][name]["chunks_sha256"] for name in reports},
        "dev_summary_sha256": sha(out / "summary.json"),
        "test_retrieval_executed_at_selection": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Selected {selected} using the predefined rule. Test retrieval has not run.")


if __name__ == "__main__":
    main()
