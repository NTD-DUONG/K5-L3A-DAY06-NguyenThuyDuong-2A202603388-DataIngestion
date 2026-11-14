"""Tạo benchmark từ các bằng chứng đã đối chiếu với corpus, không chạy retrieval."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
units = [json.loads(line) for line in (ROOT / "data/source_units.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
by_id = {unit["unit_id"]: unit for unit in units}

# split, unit ID, question, answer, evidence, type, optional scope
specs = [
    ("dev", "giay_do_u001", "Giấy dó được sản xuất từ nguyên liệu chính nào?", "Vỏ cây dó, chẳng hạn dó giấy hoặc dó liệt.", "Giấy dó là loại giấy được sản xuất từ vỏ những cây dó (như dó giấy , dó liệt ...), theo quy trình thủ công được truyền lại qua nhiều thế hệ ở một số làng nghề ở Việt Nam .", "direct", None),
    ("dev", "giay_do_u001", "Trong quy trình làm giấy dó được mô tả, vỏ dó được ngâm trong nước vôi bao lâu?", "Ba tháng.", "Vỏ cây dó được ngâm trong nước vôi với thời gian ba tháng, sau đó được nấu cách thủy khoảng 3 ngày 2 đêm cho đến khi ngửi thấy mùi thơm của vỏ cây được nấu chín nhừ hoặc thấy phần thịt của vỏ cây dó trong lại.", "direct", None),
    ("dev", "giay_do_u002", "Vì sao giấy dó nhẹ và hút mực?", "Do giấy có độ xốp.", "Vì xốp nên giấy dó rất nhẹ và hút mực.", "paraphrase", None),
    ("dev", "hoi_hoa_dan_gian_u001", "Hai loại tranh chính được nêu trong phần lịch sử hội họa dân gian Việt Nam là gì?", "Tranh Tết và tranh thờ.", "Về cơ bản có hai loại tranh chính là tranh Tết và tranh thờ .", "direct", None),
    ("dev", "hoi_hoa_dan_gian_u004", "Quan niệm tạo hình của phần lớn tranh dân gian ưu tiên ‘sống’ hay ‘giống’?", "Ưu tiên ‘sống’ hơn ‘giống’.", 'Hầu hết tranh dân gian được vẽ theo quan niệm "sống" hơn "giống".', "paraphrase", None),
    ("dev", "tranh_dong_ho_u002", "Ván in tranh Đông Hồ được chia thành hai loại nào?", "Ván in nét và ván in màu.", "Ván khắc in tranh có hai loại: ván in nét và ván in màu.", "direct", None),
    ("dev", "tranh_dong_ho_u002", "Trong phạm vi tranh Đông Hồ, ván in nét thường dùng gỗ gì?", "Gỗ thị hoặc gỗ thừng mực.", "Ván in nét thường được làm từ gỗ thị hoặc gỗ thừng mực.", "metadata", "dong_ho"),
    ("dev", "tranh_dong_ho_u002", "Vì sao người làm tranh Đông Hồ chọn gỗ mỡ cho ván in màu?", "Vì gỗ mỡ có khả năng giữ màu cao hơn nhiều loại gỗ khác.", "Ván in màu được làm bằng gỗ mỡ bởi vì khi phết màu nên để in tranh gỗ mỡ có khả năng giữ màu cao hơn nhiều loại gỗ khác.", "paraphrase", None),
    ("dev", "tranh_dong_ho_u004", "Làng Đông Hồ xưa còn có tên gọi nào?", "Làng Mái.", "Làng Đông Hồ xưa còn gọi là làng Mái.", "direct", None),
    ("dev", "tranh_hang_trong_u002", "Trong phạm vi tranh Hàng Trống, ván khắc làm bằng loại gỗ nào?", "Gỗ lồng mực hoặc gỗ thị.", "Ván khắc được làm bằng gỗ lồng mực hoặc gỗ thị.", "metadata", "hang_trong"),
    ("dev", "tranh_hang_trong_u002", "Sau khi bồi giấy tranh Hàng Trống, khi nào mới có thể vẽ màu lại?", "Khi hồ đã khô.", "Khi hồ đã khô thì mới có thể vẽ màu lại.", "condition", None),
    ("dev", "tranh_hang_trong_u002", "Khi pha màu cho tranh Hàng Trống, có bắt buộc một tỷ lệ chuẩn cố định không?", "Không; tỷ lệ nhằm tạo cảm giác thuận mắt và ưa nhìn.", "Tỷ lệ được tạo không hề đúng với công thức chuẩn mà chỉ để cho thật thuận mắt và ưa nhìn.", "condition", None),
    ("dev", "tranh_kim_hoang_u001", "Tranh Kim Hoàng còn được gọi là ‘tranh đỏ’ vì dùng những loại giấy nào?", "Giấy hồng điều hoặc giấy vàng tàu, tạo nền tươi thắm.", 'Tranh Kim Hoàng chuyên dùng giấy hồng điều hay giấy vàng tàu để làm tranh, dùng bức nền tươi thắm như vậy, cho nên tranh Kim Hoàng còn được gọi bằng một cái tên khác là "tranh đỏ", rất phù hợp với không khí tươi vui của ngày Tết.', "paraphrase", None),
    ("dev", "tranh_kim_hoang_u001", "Sự kiện năm 1915 nào góp phần khiến nghề tranh Kim Hoàng bắt đầu thất truyền?", "Trận lụt cuốn trôi nhiều ván in của làng.", "Thế kỷ 19 , tranh Kim Hoàng phát triển mạnh, nhưng rồi bắt đầu bị thất truyền từ trận lụt năm 1915, khi làng mạc từ Phùng đến Cầu Giấy bị ngập trắng, nhiều ván in tranh của làng bị cuốn trôi.", "direct", None),
    ("dev", "giay_do_u003", "Ngoài cây dó giấy, một số nơi còn dùng cây nào để làm giấy dó?", "Cây dướng và cây dó liệt.", "Một số nơi khác còn dùng cây dướng, cây dó liệt.", "direct", None),
    ("test", "tranh_lang_sinh_u002", "Với tranh làng Sình, sau khi in nét đen có được tô màu ngay không?", "Không; phải chờ bản in đen khô rồi mới tô màu.", "Bản in đen phải chờ cho khô rồi mới đem tô màu.", "condition", None),
    ("test", "tranh_lang_sinh_u002", "Trong phạm vi tranh làng Sình, bản khắc được làm bằng gỗ gì?", "Gỗ mít.", "Bản khắc của tranh được làm từ gỗ mít .", "metadata", "lang_sinh"),
    ("test", "tranh_lang_sinh_u002", "Bút vẽ tranh làng Sình được làm từ loại cây nào?", "Cây dứa mọc hoang ngoài đồng.", "Bút vẽ làm từ cây dứa mọc hoang ngoài đồng.", "direct", None),
    ("test", "khac_go_u002", "Vì sao gỗ thông là một trong những loại gỗ không thích hợp cho kỹ thuật khắc gỗ được mô tả?", "Vì có nhiều mấu và nhựa.", "Một trong số ít loại gỗ không thích hợp cho việc khắc gỗ là gỗ của cây thông ( Pinus ) vì gỗ này có nhiều mấu và nhựa.", "condition", None),
    ("test", "khac_go_u002", "Sau mỗi lần in một bản khắc gỗ, cần làm gì trước lần in tiếp theo?", "Quét mực lại cho bản khắc gỗ.", "Sau mỗi lần in phải quét mực lại cho bản in khắc gỗ.", "direct", None),
]

scopes = {
    "tranh_dong_ho": "dong_ho",
    "tranh_hang_trong": "hang_trong",
    "tranh_kim_hoang": "kim_hoang",
    "tranh_lang_sinh": "lang_sinh",
    "hoi_hoa_dan_gian": "general",
    "giay_do": "general",
    "khac_go": "general",
}
questions = []
for number, (split, uid, question, answer, quote, kind, scope) in enumerate(specs, 1):
    unit = by_id[uid]
    assert quote in unit["text"], f"Evidence missing for q{number:02d}"
    assert scope is None or scopes[unit["document_id"]] == scope
    # Lưu mọi vị trí có cùng bằng chứng nguyên văn, không chỉ trang ưu tiên.
    golds = [{"source_id": u["document_id"], "page": u["unit_id"], "evidence_quote": quote}
             for u in units if quote in u["text"] and (scope is None or scopes[u["document_id"]] == scope)]
    questions.append({
        "id": f"q{number:02d}", "split": split, "question": question,
        "expected_answer": answer, "gold_source_id": unit["document_id"],
        "gold_page": uid, "evidence_quote": quote, "acceptable_evidence": golds,
        "filter": {"painting_tradition": scope} if scope else None,
        "filter_origin": "Phạm vi dòng tranh được nêu ngay trong câu hỏi." if scope else None,
        "question_type": kind,
        "evidence_review": "AI đối chiếu nội dung và kiểm tra nguyên văn với corpus; học viên chưa duyệt.",
    })

out = ROOT / "benchmark"
out.mkdir(exist_ok=True)
payload = json.dumps(questions, ensure_ascii=False, indent=2) + "\n"
(out / "questions.json").write_text(payload, encoding="utf-8")
(out / "metadata_scopes.json").write_text(json.dumps({
    "field": "painting_tradition",
    "definition": "Phạm vi chính của tài liệu, gán từ tiêu đề; không gán theo mọi dòng tranh được nhắc tới.",
    "document_values": scopes,
    "usage": "Pipeline phải gắn cùng nhãn này cho chunk của cả A/B/C. Chỉ C dùng filter được cung cấp trước từ câu hỏi; không dùng gold_source_id/gold_page/expected_answer làm input retrieval.",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
protocol = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "questions_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    "source_units_sha256": hashlib.sha256((ROOT / "data/source_units.jsonl").read_bytes()).hexdigest(),
    "dev_ids": [q["id"] for q in questions if q["split"] == "dev"],
    "test_ids": [q["id"] for q in questions if q["split"] == "test"],
    "selection_rule": "Chọn cấu hình theo Evidence Hit@3 trên dev; nếu bằng nhau dùng Hit@1 dev; tiếp tục bằng nhau chọn ít chunk hơn; cuối cùng ưu tiên A rồi B rồi C. Cố định trước khi chạy test.",
    "split_rationale": "Dev tập trung giấy dó, tổng quan, Đông Hồ, Hàng Trống, Kim Hoàng. Test dành cho kỹ thuật làng Sình và khắc gỗ; chưa chạy retrieval để chọn câu.",
    "limitations": ["Chỉ 5 câu test, không đại diện mọi nguồn.", "Corpus tổng quan nhắc lại các dòng tranh nên vẫn có giao thoa chủ đề dev/test.", "Gold do AI hỗ trợ, học viên cần đọc và xác nhận; chưa có nhãn đánh giá thủ công retrieval.", "Các evidence tương đương khác phải được xem xét thủ công và ghi lại, không tự coi sai vì khác nguồn."]
}
(out / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
assert sum(q["split"] == "dev" for q in questions) == 15
assert sum(q["split"] == "test" for q in questions) == 5
assert sum(q["filter"] is not None for q in questions) >= 3
assert any(q["split"] == "test" and q["filter"] for q in questions)
print("20 questions: 15 dev / 5 test; 3 metadata filters including 1 test.")
print("Every evidence quote verified against its source unit. No retrieval executed.")
