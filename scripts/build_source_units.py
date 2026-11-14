from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed"
OUTPUT = ROOT / "data/source_units.jsonl"
MIN_CHARS = 1500

all_units = []

for path in sorted(INPUT.glob("*.txt")):
    text = path.read_text(encoding="utf-8")
    boundaries = []
    start = 0

    while len(text) - start >= MIN_CHARS:
        minimum_end = start + MIN_CHARS

        # Ưu tiên kết thúc ở ranh giới câu hoặc đoạn.
        match = re.search(r'[.!?](?=\s)|\n\n', text[minimum_end:])

        if match is None:
            end = len(text)
        else:
            end = minimum_end + match.end()

        # Gộp phần đuôi nếu nó ngắn hơn 1.500 ký tự.
        if len(text) - end < MIN_CHARS:
            end = len(text)

        boundaries.append((start, end))
        start = end

    if start < len(text):
        if boundaries:
            previous_start, _ = boundaries[-1]
            boundaries[-1] = (previous_start, len(text))
        else:
            print(f"Không tính nguồn quá ngắn: {path.name}")
            continue

    for number, (start, end) in enumerate(boundaries, 1):
        unit_text = text[start:end]

        all_units.append({
            "unit_id": f"{path.stem}_u{number:03d}",
            "document_id": path.stem,
            "source_text_path": path.relative_to(ROOT).as_posix(),
            "start_char": start,
            "end_char": end,
            "char_count": len(unit_text),
            "text": unit_text,
        })

    print(f"{path.name}: {len(boundaries)} đơn vị")

with OUTPUT.open("w", encoding="utf-8") as file:
    for unit in all_units:
        file.write(json.dumps(unit, ensure_ascii=False) + "\n")

assert all(unit["char_count"] >= MIN_CHARS for unit in all_units)
assert len({unit["unit_id"] for unit in all_units}) == len(all_units)

print(f"\nTổng: {len(all_units)} đơn vị")
print(f"Đã lưu: {OUTPUT}")

if len(all_units) >= 30:
    print("Đạt số lượng sơ bộ; còn kiểm tra nội dung và trùng lặp.")
else:
    print("Chưa đủ 30 đơn vị, cần bổ sung dữ liệu.")