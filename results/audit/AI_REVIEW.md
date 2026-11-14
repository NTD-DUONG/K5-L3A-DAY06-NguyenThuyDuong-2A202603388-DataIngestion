# Kết quả chấm của AI

Người chấm: Codex AI. Học viên chưa xác nhận; không gọi đây là nhãn thủ công của học viên. Phương pháp, thiên lệch và từng lý do nằm trong ai_summary.json / ai_assessments.jsonl.

| Cấu hình | Test Hit@1 sau AI review | Test Hit@3 sau AI review | Coherence /2 (10 mẫu) | Grounding 0/1/2 (5 câu) | Grounding TB /2 | Metadata đủ/đúng |
|---|---:|---:|---:|---|---:|---:|
| A | 2/5 | 2/5 | 1.00 | 2/1/2 | 1.00 | 15/15 |
| B | 1/5 | 2/5 | 1.70 | 3/0/2 | 0.80 | 15/15 |
| C | 1/5 | 3/5 | 1.70 | 2/0/3 | 1.20 | 15/15 |

Chỉ q16 được bổ sung evidence tương đương ở top-1 cho cả A/B/C. Giữ nguyên câu hỏi, cấu hình, trace và chỉ số tự động trong results/test; file *_test_ai_reviewed.jsonl lưu tách biệt từng quyết định. Lựa chọn C từ dev giữ nguyên.

Grounding C theo thứ tự q16–q20: 2, 2, 0, 0, 2. AI nhận đủ bằng chứng cho q16/q17/q20; q18 thiếu cây dứa, q19 thiếu nguyên nhân gỗ thông không thích hợp.

Yêu cầu học viên đọc hiểu và xác nhận/chấm thủ công vẫn còn. Các trường human trong packet gốc giữ nguyên trạng thái.
