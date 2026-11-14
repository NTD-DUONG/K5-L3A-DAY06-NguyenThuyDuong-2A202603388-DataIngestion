# Day 06 · Data Ingestion Engineering

## Bài làm hiện tại

Corpus: **Tranh Đông Hồ và hội họa dân gian Việt Nam** — 7 nguồn, 30 đơn vị HTML/MHTML, 52.822 ký tự chuẩn hóa. Đã chạy pipeline embedding local + Chroma và benchmark 15 dev / 5 test cho A/B/C. Chọn C bằng dev trước khi chạy test.

- [Hướng dẫn setup và chạy](PIPELINE.md), dependencies trong [requirements-lab.txt](requirements-lab.txt).
- [Manifest nguồn và giấy phép](data/manifest.json), [bộ câu hỏi](benchmark/questions.json), [cấu hình](configs/strategies.json).
- Kết quả: [dev](results/dev/summary.json), [test](results/test/summary.json), [lựa chọn cố định](results/dev_selection.json).
- [Báo cáo cá nhân](report/individual/2A202603388_NguyenThuyDuong.md) và [phiếu audit](results/audit/CHAM_DOC_TUNG_MAU.md).
- [Kết quả AI chấm riêng](results/audit/AI_REVIEW.md): đủ nhận xét coherence/metadata/grounding, có khai báo phương pháp và giới hạn; chưa phải nhãn thủ công của học viên.
- [Phiếu đọc và chấm từng mẫu](results/audit/CHAM_DOC_TUNG_MAU.md): nhận xét cụ thể 10 vị trí coherence, 5 câu grounding mỗi cấu hình và 45 metadata.

Kiểm tra bài từ thư mục repo bằng `python scripts/validate_submission.py`. Nguyễn Thùy Dương đã xác nhận 30 nhãn coherence, 15 grounding, 45 metadata và evidence tương đương q16. Hồ sơ xác nhận và tổng hợp được lưu trong thư mục audit. [Xác nhận](results/audit/student_confirmation.json), [tổng hợp nhãn](results/audit/HUMAN_SUMMARY.md).

Bản nguồn nộp trong `data/text_sources/` chứa văn bản Wikipedia và liên kết nguồn. Quy trình đóng gói đã loại ảnh, CSS và nội dung thực thi. Bản báo cáo mô tả phương pháp, công cụ và giới hạn của đánh giá. Phiên bản bài nộp được gắn tag `submission-day06-v3`. Nội dung bên dưới là đề bài gốc.

**Lab cá nhân** · **4 giờ** · **Dữ liệu tự chọn**

Biến tài liệu thành kho tri thức có thể truy xuất cho AI agent, rồi đo xem cách chuẩn bị dữ liệu nào hiệu quả nhất.

| 📄 Dữ liệu | 🧩 Chiến lược | 🎯 Benchmark |
|---|---|---|
| Tối thiểu **30 trang nội dung** | Tối thiểu **3 cấu hình** | Tối thiểu **20 câu hỏi** |

## Bắt đầu nhanh

Dùng [starter PostgreSQL + pgvector](starter/README.md) để dựng database và hoàn thiện các hàm TODO, hoặc tự chọn vector store tương đương. Starter chỉ là khung: **bạn tự hiện thực pipeline và benchmark**.

## 1. Xây pipeline

![Đọc tài liệu, chuẩn hóa, chia chunk, tạo vector, lưu và kiểm tra](assets/ingestion-pipeline.svg)

Chọn tài liệu được phép sử dụng; giữ **ID tài liệu, nguồn, trang/vị trí** và metadata phù hợp. Dùng embedding model thật qua API hoặc chạy local; lưu và truy xuất bằng pgvector, Qdrant, Chroma hoặc một store tương đương.

## 2. So sánh và đánh giá

![Ba chiến lược được đánh giá trên cùng corpus và benchmark dev/test](assets/benchmark-workflow.svg)

Dùng cùng dữ liệu, model và câu hỏi cho cả ba cấu hình. Tách **15 câu dev / 5 câu test** trước khi chạy; chọn cấu hình trên dev, rồi đánh giá test sau khi cố định. Mỗi câu hỏi cần có đoạn bằng chứng và trang nguồn; thiết kế bộ câu hỏi và đánh giá theo [BENCHMARK.md](BENCHMARK.md).

Đánh giá theo năm khía cạnh: **độ chính xác truy xuất**, **tính mạch lạc của chunk**, **tính hữu dụng của metadata**, **chất lượng grounding** và **tác động của chiến lược dữ liệu**. Giải thích lựa chọn bằng kết quả, ví dụ lỗi và các đánh đổi.

## 3. Chuẩn bị bài nộp

1. Chạy pipeline và lưu cấu hình, kết quả top-3, trace cùng nhãn đánh giá thủ công.
2. Điền [thông tin học viên](STUDENT.md), [nhật ký thí nghiệm](artifacts/experiment_log.csv) và bản sao [mẫu báo cáo cá nhân](report/individual/MSSV_HoTen.md).
3. Kiểm tra mã nguồn, cách chạy, manifest dữ liệu và checklist trong [SUBMISSION.md](SUBMISSION.md).

## Tài liệu hướng dẫn

| Bạn cần tìm | Tài liệu |
|---|---|
| Setup baseline PostgreSQL + pgvector | [starter/README.md](starter/README.md) |
| Các bước làm và cách tính chỉ số | [GUIDE.md](GUIDE.md) |
| Tiến độ trong 4 giờ | [CHECKPOINTS.md](CHECKPOINTS.md) |
| Năm tiêu chí benchmark và bộ câu hỏi | [BENCHMARK.md](BENCHMARK.md) |
| Tiêu chí chấm điểm | [RUBRIC.md](RUBRIC.md) |
| Quy tắc sử dụng dữ liệu, AI và API | [RULES.md](RULES.md) |
| Cách nộp bài | [SUBMISSION.md](SUBMISSION.md) |

[data/format-example.json](data/format-example.json) chỉ minh họa định dạng, không phải corpus đủ điều kiện. Phần xử lý và benchmark do bạn tự hiện thực; không bắt buộc xây chatbot.
