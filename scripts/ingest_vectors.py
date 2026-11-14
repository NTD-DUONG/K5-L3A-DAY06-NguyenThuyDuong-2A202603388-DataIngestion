"""Embed chunk snapshots, persist in Chroma, verify reload without duplicates."""
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from starter.src.embeddings import MyEmbedder
from starter.src.chroma_store import ChromaStore


def main():
    parser = argparse.ArgumentParser(description="Embed chunks and persist in Chroma")
    parser.add_argument("--results-dir", default="results", help="Report directory relative to the repo")
    parser.add_argument("--database-dir", default=".runtime/chroma", help="Chroma directory relative to the repo")
    args = parser.parse_args()
    results_dir = (ROOT / args.results_dir).resolve()
    store_path = (ROOT / args.database_dir).resolve()
    results_dir.relative_to(ROOT)
    database_relative_path = store_path.relative_to(ROOT).as_posix()
    output = results_dir / "ingestion"
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    embedder = MyEmbedder("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    config = embedder.configuration
    signature = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    store = ChromaStore(store_path, embedder.dimensions, signature)
    records, cache = {}, {}
    for strategy in ["A", "B", "C"]:
        raw = (ROOT / f"artifacts/chunks/{strategy}.jsonl").read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        reused = digest in cache
        begin = time.perf_counter()
        if reused:
            vectors, stats = cache[digest]
        else:
            print(f"Embedding {strategy}: {len(rows)} chunks", flush=True)
            vectors = embedder.embed_documents([row["text"] for row in rows])
            stats = dict(embedder.last_stats)
            cache[digest] = (vectors, stats)
        embedding_seconds = time.perf_counter() - begin
        begin = time.perf_counter()
        first = store.sync(strategy, rows, vectors)
        storage_seconds = time.perf_counter() - begin
        second = store.sync(strategy, rows, vectors)
        assert second["before"] == second["after"] == len(rows)
        fetched = store.collection(strategy).get(include=["documents", "metadatas"])
        expected = {row["chunk_id"]: row for row in rows}
        for cid, text, metadata in zip(fetched["ids"], fetched["documents"], fetched["metadatas"]):
            assert text == expected[cid]["text"]
            assert metadata == expected[cid]["metadata"]
        records[strategy] = {
            "chunks_sha256": digest, "chunk_count": len(rows),
            "embedding_stats": stats, "embeddings_reused_from_B": reused,
            "embedding_seconds_this_run": embedding_seconds,
            "storage_sync_seconds": storage_seconds,
            "first_sync": first, "repeat_sync": second,
            "stored_documents_and_metadata_match": True,
        }
        print(f"{strategy}: stored {len(rows)}; repeated sync count unchanged", flush=True)

    # A technical smoke query, separate from the 20 benchmark questions.
    query = "Kỹ thuật và vật liệu tạo nên tranh dân gian."
    vector = embedder.embed_query(query)
    smoke = store.search("C", vector, filters={"painting_tradition": "dong_ho"})
    assert len(smoke) == 3 and all(row["metadata"]["painting_tradition"] == "dong_ho" for row in smoke)
    report = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": config, "model_signature": signature,
        "libraries": {name: version(name) for name in ["sentence-transformers", "chromadb", "torch", "transformers", "numpy"]},
        "vector_store": {"backend": "Chroma PersistentClient", "path": database_relative_path, "metric": "cosine", "search": "HNSW approximate nearest neighbor; ef_search=100"},
        "strategies": records, "total_run_seconds": time.perf_counter() - started,
        "external_api_cost": 0, "cost_note": "Local inference; excludes electricity, hardware and prior model download.",
        "smoke_check": {"query": query, "strategy": "C", "filter": {"painting_tradition": "dong_ho"}, "returned": len(smoke), "all_obey_filter": True},
        "benchmark_executed": False,
        "limitations": ["Token-window pooling is a custom representation used identically for all strategies, rather than the model default truncation.", "Repeated sync validates stable counts, not independent manual metadata or grounding evaluation.", "C reuses B embeddings; per-strategy embedding times are not independent cold-run comparisons.", "If a document changes, regenerate units and chunks, then sync removes IDs absent from the new strategy snapshot. Model changes require a new database directory."]
    }
    (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {output.relative_to(ROOT).as_posix()}/summary.json")


if __name__ == "__main__":
    main()
