"""Single entry point for the implemented local Chroma lab pipeline."""
import argparse
from pathlib import Path
import subprocess
import sys


def main() -> None:
    stages = {
        "check": "validate_submission.py", "units": "build_source_units.py",
        "chunks": "build_chunks.py", "ingest": "ingest_vectors.py",
        "dev": "evaluate_dev.py", "test": "evaluate_test.py",
        "prepare-audit": "prepare_audits.py", "audit-status": "summarize_audits.py",
        "draft-report": "build_report.py",
    }
    parser = argparse.ArgumentParser(description="Day 6: local embeddings + persistent Chroma")
    parser.add_argument("--stage", choices=stages, default="check")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, str(root / "scripts" / stages[args.stage])], cwd=root)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
