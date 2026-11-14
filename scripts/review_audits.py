"""Interactive student annotation. No automatic copying of AI proposals."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results/audit"
TASKS = {
    "coherence": ("coherence.jsonl", "human_score"),
    "grounding": ("grounding.jsonl", "human_score"),
    "metadata": ("metadata.jsonl", "human_complete_and_correct"),
}


def main():
    parser = argparse.ArgumentParser(description="Đọc bằng chứng rồi nhập nhãn học viên; q để dừng và tiếp tục sau")
    parser.add_argument("--task", choices=TASKS, required=True)
    parser.add_argument("--reviewer", required=True, help="Tên thật người đọc/chấm các mẫu")
    parser.add_argument("--strategy", choices=["A", "B", "C"])
    args = parser.parse_args()
    if not args.reviewer.strip():
        parser.error("Cần tên người chấm")
    name, field = TASKS[args.task]
    path = AUDIT / name
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print("Hãy đọc nội dung thực tế. Nhập q để dừng; các nhãn đã nhập được lưu ngay.")
    print("0: thiếu ý/bằng chứng; 1: một phần; 2: đầy đủ. Metadata: y=đủ và đúng, n=có lỗi.")
    for row in rows:
        if row[field] is not None or (args.strategy and row["strategy"] != args.strategy):
            continue
        print("\n" + "=" * 65)
        print(row["strategy"], row.get("question_id", row.get("sample_id")), "rank", row.get("rank", ""))
        if args.task == "coherence":
            print("Nguồn/unit:", row["unit_id"], "anchor:", row["anchor_offset"])
            print("Chunk cần chấm:\n", row["chunk"]["text"])
            print("\nNgữ cảnh nguồn để đối chiếu:\n", row["source_context"])
        elif args.task == "grounding":
            print("Câu hỏi:", row["question"])
            print("Đáp án tham chiếu:", row["expected_answer"])
            print("Evidence gold:", row["gold_quote"])
            for rank, hit in enumerate(row["hits"], 1):
                print(f"\nTop-{rank} ({hit['metadata']['page']}):\n{hit['text']}")
                print("Nguồn:", hit["metadata"]["snapshot_url"])
        else:
            print("Metadata:\n", json.dumps(row["metadata"], ensure_ascii=False, indent=2))
            print("Nội dung:\n", row["text"])
            print("Nguồn đối chiếu:", row["source_reference"])
            print("Hãy đối chiếu source, unit và phạm vi dòng tranh với nguồn.")

        allowed = {"y": True, "n": False} if args.task == "metadata" else {"0": 0, "1": 1, "2": 2}
        while True:
            answer = input("Nhãn (y/n hoặc 0/1/2; q để dừng): ").strip().lower()
            if answer == "q":
                return
            if answer in allowed:
                break
            print("Giá trị không hợp lệ.")
        reason = input("Lý do sau khi đọc: ").strip()
        if not reason:
            print("Chưa có lý do; không lưu mẫu này. Chạy lại để tiếp tục.")
            return
        row[field] = allowed[answer]
        row["human_reason"] = reason
        row["reviewer"] = args.reviewer.strip()
        row["reviewed_at_utc"] = datetime.now(timezone.utc).isoformat()
        temporary = path.with_suffix(".jsonl.tmp")
        temporary.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows), encoding="utf-8")
        temporary.replace(path)
        print("Đã lưu nhãn.")
    print("Đã hết các mẫu chưa chấm trong phạm vi đã chọn.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nĐã dừng; các nhãn đã lưu vẫn được giữ.")
