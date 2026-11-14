from pathlib import Path
from email import policy
from email.parser import BytesParser
import unicodedata
import argparse
import json

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("input_name", help="Tên file trong data/text_sources hoặc đường dẫn tương đối từ repo")
parser.add_argument("output_name", help="Tên file trong data/processed")
parser.add_argument("--check", action="store_true", help="Đối chiếu với văn bản hiện có")
args = parser.parse_args()

input_path = Path(args.input_name)
source = ROOT / input_path if len(input_path.parts) > 1 else ROOT / "data/text_sources" / input_path
if not source.exists() and len(input_path.parts) == 1:
    source = ROOT / "data/raw" / input_path
raw = source.read_bytes()

# Hỗ trợ cả HTML thông thường và trang lưu dạng MHTML.
message = BytesParser(policy=policy.default).parsebytes(raw)

if message.is_multipart():
    html_part = next(
        (
            part for part in message.walk()
            if part.get_content_type() == "text/html"
        ),
        None,
    )
    if html_part is None:
        raise ValueError("Không tìm thấy phần HTML trong tài liệu.")
    html = html_part.get_payload(decode=True).decode("utf-8")
else:
    html = raw.decode("utf-8-sig")

soup = BeautifulSoup(html, "html.parser")
content = soup.select_one("#mw-content-text .mw-parser-output")

if content is None:
    raise ValueError("Không tìm thấy nội dung bài Wikipedia.")

# Loại các thành phần không phải nội dung chính.
for element in content.select(
    "script, style, table, figure, .mw-editsection, "
    ".reference, .reflist, .navbox, .thumb, .gallery"
):
    element.decompose()

paragraphs = []
excluded_blocks = []
skip_section_level = None

for element in content.find_all(["h2", "h3", "h4", "p", "li", "dt", "dd"]):
    # Không lấy trùng nội dung của các danh sách lồng nhau.
    if element.name == "li" and element.find_parent("li"):
        continue

    text = unicodedata.normalize("NFC", element.get_text(" ", strip=True))
    text = " ".join(text.split())

    if element.name.startswith("h") and text in {
        "Tham khảo", "Chú thích", "Liên kết ngoài", "Xem thêm"
    }:
        break

    # Chỉ lọc các đoạn lệch chủ đề trong nguồn Khắc gỗ.
    if source.stem == "khac_go":
        heading_level = int(element.name[1]) if element.name.startswith("h") else None
        if skip_section_level is not None:
            if heading_level is not None and heading_level <= skip_section_level:
                skip_section_level = None
            else:
                if text:
                    excluded_blocks.append({"text": text, "reason": "Ứng dụng in lên đồ vật, ngoài phạm vi in tranh"})
                continue
        if heading_level is not None and text == "Ứng dụng":
            skip_section_level = heading_level
            excluded_blocks.append({"text": text, "reason": "Tiêu đề phần ứng dụng ngoài phạm vi"})
            continue
        if text == "Các ứng dụng khắc gỗ hiện đại:" or text.startswith('"Khắc bút chì:'):
            excluded_blocks.append({"text": text, "reason": "Khắc bút chì không thuộc kỹ thuật in tranh"})
            continue

    if text:
        paragraphs.append(text)

text = "\n\n".join(paragraphs)

output = ROOT / "data/processed" / args.output_name
if args.check:
    if text != output.read_text(encoding="utf-8"):
        raise ValueError(f"Nội dung trích xuất khác corpus đã chốt: {source.name}")
    print(f"MATCH {source.name}: {len(text)} ký tự")
    raise SystemExit(0)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(text, encoding="utf-8")

if source.stem == "khac_go":
    audit_path = ROOT / "data/processing_logs/khac_go_filter.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps({
        "source": source.relative_to(ROOT).as_posix(),
        "output": output.relative_to(ROOT).as_posix(),
        "excluded_blocks": excluded_blocks,
        "retained_scope": "Kỹ thuật, vật liệu, dụng cụ và lịch sử in khắc gỗ làm tài liệu nền",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Đã lưu: {output}")
print(f"Số ký tự: {len(text):,}")
print("\nXem trước:\n")
print(text[:800])
