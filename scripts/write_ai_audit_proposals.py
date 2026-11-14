"""Record explicitly AI-authored proposals after reading selected source/trace texts."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/audit"


def load(name):
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


# Judgments authored after reading all selected A/B texts (C identical to B).
coherence_b = {
    "coh01": (2, "Giữ trọn các câu mô tả quy trình từ nguyên liệu tới liềm xeo; chủ đề giấy dó rõ."),
    "coh02": (2, "Giữ các câu hoàn chỉnh về cấu trúc, độ bền và làng nghề giấy dó; đủ chủ thể."),
    "coh03": (1, "Phần đặc tính giấy đọc hiểu được, nhưng cuối chunk treo tiêu đề Cây dó giấy chưa có nội dung."),
    "coh04": (2, "Có định nghĩa và lịch sử, giữ đầy đủ chủ thể tranh dân gian và các câu hoàn chỉnh."),
    "coh05": (2, "Các đoạn mô tả nét riêng và đặc điểm tạo hình có đủ ngữ cảnh; tiêu đề cuối báo chủ đề tiếp theo."),
    "coh06": (2, "Giữ trọn mô tả giấy dó/giấy điệp, tính chất và nguyên liệu tạo màu; các câu tự hiểu được."),
    "coh07": (2, "Các đoạn bố cục, đề tài và ví dụ truyện Nôm giữ trọn câu và chủ thể."),
    "coh08": (2, "Giữ đầy đủ ý nghĩa tranh gà và Đám cưới chuột, có ví dụ và giải thích trong chunk."),
    "coh09": (1, "Nội dung tổng quan và danh sách dòng tranh rõ, nhưng kết thúc bằng tiêu đề Đông Hồ chưa có phần giải thích."),
    "coh10": (1, "Đầu chunk dùng Dòng tranh này cần ngữ cảnh trước; phía sau xác định Đông Hồ, nhưng cuối treo tiêu đề Hàng Trống."),
}
coherence_a = {
    "coh01": "Đầu cắt giữa Kinh thành, cuối dừng ở để; quy trình chỉ còn một phần dù các bước ở giữa đọc được.",
    "coh02": "Đầu cắt giữa miếu thờ, cuối cắt mô tả giấy mịn; một số ý làng nghề vẫn đọc được.",
    "coh03": "Đầu thiếu phần mở câu, cuối cắt Nguyên liệu chủ; đặc tính giấy còn hiểu được một phần.",
    "coh04": "Đầu là phần nối thiếu tiền đề của chúng; cuối cắt câu lịch sử tiếp theo, các câu nhà Lý/Trần còn đầy đủ.",
    "coh05": "Đầu mất chủ thể Tranh dân gian, cuối cắt giữa ngày; ý tạo hình đọc được nhưng thiếu ngữ cảnh.",
    "coh06": "Đầu cắt từ loại, cuối cắt tranh; có mô tả tính chất giấy nhưng thiếu câu giới thiệu nguyên vẹn.",
    "coh07": "Đầu bắt đầu giữa câu gắn bó, cuối cắt trống; ví dụ truyện Nôm vẫn đọc được.",
    "coh08": "Đầu cắt từ ngày, cuối câu bị cắt; đoạn Đám cưới chuột vẫn giữ đủ ý.",
    "coh09": "Đầu cắt từ nhanh; danh sách dòng tranh và ý bảo tồn đọc được nhưng thiếu đầu đoạn.",
    "coh10": "Đầu cắt nông thôn, cuối cắt danh sách tác phẩm; ý về Đông Hồ ở giữa còn hiểu được.",
}

coherence = []
for row in load("coherence.jsonl"):
    score, reason = (1, coherence_a[row["sample_id"]]) if row["strategy"] == "A" else coherence_b[row["sample_id"]]
    coherence.append({"sample_id": row["sample_id"], "strategy": row["strategy"],
                      "chunk_id": row["chunk"]["chunk_id"], "ai_proposed_score": score,
                      "ai_reason": reason, "human_confirmed": False})

grounding = []
for row in load("grounding.jsonl"):
    qid, strategy = row["question_id"], row["strategy"]
    if qid == "q16":
        score, reason = 2, "Top-1 nguồn tổng quan ghi Bản in đen chờ cho khô thì đem tô màu và nêu rõ tranh làng Sình ngay sau đó; đủ điều kiện, có metadata truy nguồn."
    elif qid == "q17":
        if strategy == "C":
            score, reason = 2, "Top-2 ghi rõ bản khắc làm từ gỗ mít, nguồn tranh làng Sình và unit/offset truy vết được."
        else:
            score, reason = 0, "Top-3 nói về khắc gỗ tổng quát/châu Âu, không nêu gỗ mít cho tranh làng Sình."
    elif qid == "q18":
        score, reason = 0, "Top-3 không có chi tiết bút vẽ làm từ cây dứa; chỉ trả về mô tả tranh hoặc dụng cụ khác."
    elif qid == "q19":
        if strategy == "A":
            score, reason = 1, "Top-3 có mảnh câu (Pinus) vì gỗ này có nhiều mấu và nhựa nhưng mất chủ thể gỗ thông và phần khẳng định không thích hợp. Không tính đủ evidence trong một chunk."
        else:
            score, reason = 0, "Các chunk nói về vân gỗ, dụng cụ hoặc hoàng dương; không chứa lý do loại gỗ thông."
    else:
        assert qid == "q20"
        score, reason = 2, "Có nguyên câu Sau mỗi lần in phải quét mực lại cho bản in khắc gỗ, đúng nguồn và đủ ngữ cảnh."
    grounding.append({"strategy": strategy, "question_id": qid, "ai_proposed_score": score,
                      "ai_reason": reason, "human_confirmed": False})

equivalent = []
for strategy in ["A", "B", "C"]:
    traces = [json.loads(line) for line in (ROOT / f"results/test/{strategy}_traces.jsonl").read_text(encoding="utf-8").splitlines()]
    row = next(t for t in traces if t["question_id"] == "q16")
    hit = row["hits"][0]
    quote = "Bản in đen chờ cho khô thì đem tô màu."
    assert quote in hit["text"] and "tranh làng Sình" in hit["text"]
    equivalent.append({
        "strategy": strategy, "question_id": "q16", "rank": 1,
        "chunk_id": hit["chunk_id"], "source_id": hit["metadata"]["document_id"],
        "unit_id": hit["metadata"]["page"], "evidence_quote": quote,
        "snapshot_url": hit["metadata"]["snapshot_url"],
        "ai_proposed_equivalent_hit": True, "human_confirmed": False,
        "reason": "Cùng điều kiện phải để bản in đen khô trước tô màu; văn cảnh xác định tranh làng Sình.",
    })

summary = {"author": "Codex AI; not student/manual labels", "human_review_pending": True,
           "automatic_metrics_preserved": True, "coherence_proposals": coherence,
           "grounding_proposals": grounding, "equivalent_evidence_proposals": equivalent}
(OUT / "ai_proposals.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# Phiếu rà soát — học viên cần đọc và xác nhận",
    "",
    "Các điểm dưới đây do Codex AI đề xuất sau khi đọc mẫu và trace. Chưa phải nhãn thủ công của học viên; không báo cáo chúng như đã được học viên chấm. Không thay đổi cấu hình theo test.",
    "",
    "## Grounding: 5 câu test × 3 cấu hình",
    "",
    "0 = không có bằng chứng; 1 = có nhưng thiếu điều kiện/ngữ cảnh; 2 = đủ để trả lời và truy nguồn. Grounding đánh giá bằng chứng truy xuất, không đánh giá độ chính xác câu trả lời LLM.",
    "",
    "| Cấu hình | Câu | AI đề xuất /2 | Lý do | Điểm học viên /2 |",
    "|---|---|---:|---|---|",
]
for row in grounding:
    lines.append(f"| {row['strategy']} | {row['question_id']} | {row['ai_proposed_score']} | {row['ai_reason']} | |")
lines += ["", "Xem đầy đủ câu hỏi, đáp án và top-3 trong `grounding.jsonl`. Điền `human_score`, `human_reason`, `reviewer` sau khi đọc; có thể sửa điểm AI đề xuất.", "", "## Coherence: cùng 10 vị trí nguồn", "",
          "0 = bị cắt/thiếu chủ thể khiến không hiểu; 1 = hiểu một phần nhưng thiếu ngữ cảnh; 2 = tự hiểu được và giữ trọn ý. Quy tắc chọn mẫu ở `protocol.json` được ghi sau retrieval, trước khi gán các điểm này; không coi là chấm mù.", "",
          "| Mẫu | Cấu hình | AI đề xuất /2 | Lý do | Điểm học viên /2 |", "|---|---|---:|---|---|"]
for row in coherence:
    lines.append(f"| {row['sample_id']} | {row['strategy']} | {row['ai_proposed_score']} | {row['ai_reason']} | |")
lines += ["", "Xem chunk đầy đủ và ngữ cảnh trong `coherence.jsonl`. Điền các trường human sau khi đọc. Mẫu đầu bảng tập trung giấy dó/tổng quan, không đại diện ngẫu nhiên toàn corpus.", "", "## Metadata", "",
          "`metadata.jsonl` chứa 45 bản ghi (5 câu × top-3 × 3 cấu hình). Các kiểm tra máy đối chiếu URL, unit, snapshot, offset và nhãn dòng tranh đều đạt 15/15 mỗi cấu hình. Đây là độ nhất quán tự động với manifest, chưa phải 15/15 đã chấm thủ công.", "",
          "Học viên đối chiếu trang nguồn qua snapshot và nội dung unit, rồi điền `human_complete_and_correct` (true/false), `human_reason`, `reviewer`.", "",
          "Trường source/page/offset giúp truy vết. Trường painting_tradition giúp C giới hạn q17 vào làng Sình. Hạn chế: nhãn là phạm vi chính của tài liệu; nguồn tổng quan mang nhãn general dù có đoạn về làng Sình, nên filter có thể loại bằng chứng hữu ích.", "",
          "## Bằng chứng tương đương q16", "",
          "Top-1 của cả A/B/C có câu “Bản in đen chờ cho khô thì đem tô màu.” trong nguồn Hội họa dân gian Việt Nam; đoạn kế tiếp xác định tranh làng Sình. AI đề xuất chấp nhận đây là bằng chứng tương đương. Chi tiết ở `ai_proposals.json`; bộ câu hỏi và số liệu tự động ban đầu được giữ nguyên.", "",
          "Nếu học viên xác nhận trường hợp q16, số test sau review sẽ là A Hit@1 2/5, Hit@3 2/5; B 1/5 và 2/5; C 1/5 và 3/5. Các con số này chỉ là dự kiến theo đề xuất AI, chưa phải kết quả review đã được xác nhận.", "",
          "Không dùng các ô human còn trống để tính trung bình; chưa hoàn thành audit khi chưa có người chấm thật.", ""]
(OUT / "REVIEW.md").write_text("\n".join(lines), encoding="utf-8")
print("Saved AI proposals and REVIEW.md; human labels remain blank.")
