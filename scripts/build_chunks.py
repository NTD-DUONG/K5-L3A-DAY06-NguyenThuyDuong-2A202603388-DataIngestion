"""Build A/B/C chunk artifacts without embeddings or benchmark retrieval."""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from starter.src.chunking import fixed_size, by_paragraph
from starter.src.models import DocumentPage


def main():
    configs = json.loads((ROOT / "configs/strategies.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    docs = {doc["source_id"]: doc for doc in manifest["documents"]}
    scopes = json.loads((ROOT / "benchmark/metadata_scopes.json").read_text(encoding="utf-8"))["document_values"]
    unit_bytes = (ROOT / manifest["source_units_path"]).read_bytes()
    units = [json.loads(line) for line in unit_bytes.decode("utf-8").splitlines() if line.strip()]
    out = ROOT / "artifacts/chunks"
    out.mkdir(parents=True, exist_ok=True)
    reports = {}
    all_chunks = {}
    for strategy, config in configs.items():
        started = time.perf_counter()
        chunks = []
        for unit in units:
            doc = docs[unit["document_id"]]
            page = DocumentPage(
                document_id=unit["document_id"], source=doc["source_path_or_url"],
                page=unit["unit_id"], text=unit["text"],
                metadata={
                    "painting_tradition": scopes[unit["document_id"]],
                    "title": doc["title"], "language": manifest["language"],
                    "snapshot_url": doc["snapshot_url"],
                    "unit_start_char": unit["start_char"],
                    "source_text_path": unit["source_text_path"],
                },
            )
            if config["chunk_method"] == "fixed":
                items = fixed_size(page, config["chunk_size_chars"], config["overlap_chars"])
                limit = config["chunk_size_chars"]
            elif config["chunk_method"] == "paragraph":
                items = by_paragraph(page, config["max_chunk_size_chars"])
                limit = config["max_chunk_size_chars"]
            else:
                raise ValueError(f"Unknown chunk method: {config['chunk_method']}")

            covered = bytearray(len(page.text))
            for chunk in items:
                start, end = chunk.metadata["unit_start_offset"], chunk.metadata["unit_end_offset"]
                assert chunk.text == page.text[start:end]
                assert 0 < len(chunk.text) <= limit
                assert chunk.metadata["painting_tradition"] == scopes[page.document_id]
                covered[start:end] = b'\x01' * (end - start)
            assert all(covered[i] or char.isspace() for i, char in enumerate(page.text)), page.page
            chunks.extend(items)

        assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
        rows = [asdict(chunk) for chunk in chunks]
        all_chunks[strategy] = rows
        (out / f"{strategy}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        lengths = [len(chunk.text) for chunk in chunks]
        reports[strategy] = {
            "config": config, "unit_count": len(units), "chunk_count": len(chunks),
            "min_chars": min(lengths), "max_chars": max(lengths),
            "mean_chars": statistics.mean(lengths), "median_chars": statistics.median(lengths),
            "total_chunk_chars": sum(lengths), "chunking_seconds": time.perf_counter() - started,
        }
        print(f"{strategy}: {len(chunks)} chunks; {min(lengths)}-{max(lengths)} characters")

    assert {k: v for k, v in configs["B"].items() if k != "use_metadata_filter"} == {k: v for k, v in configs["C"].items() if k != "use_metadata_filter"}
    assert all_chunks["B"] == all_chunks["C"], "B/C must use identical chunks"
    report = {
        "source_units_sha256": hashlib.sha256(unit_bytes).hexdigest(),
        "strategies": reports,
        "checks": {"source_offsets_match": True, "all_nonwhitespace_covered": True, "unique_ids_per_strategy": True, "B_C_identical": True},
        "notes": [
            "Timing covers only chunk construction, validation and artifact serialization; not embedding or database ingestion.",
            "Chunks stay within source units; unit boundaries can already split source paragraphs.",
            "B prefers paragraph and sentence boundaries but oversized paragraphs may split at words.",
            "Character limits do not guarantee tokenizer limits; check model token lengths before embedding.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Verified source offsets, coverage, size limits, IDs, and identical B/C chunks.")


if __name__ == "__main__":
    main()
