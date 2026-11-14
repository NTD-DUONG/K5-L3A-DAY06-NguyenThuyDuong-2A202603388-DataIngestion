# Setup và chạy bài lab

Nguyễn Thùy Dương, MSSV 2A202603388, lớp L3A. Bản bài nộp được gắn tag `submission-day06` trên repo công khai. [Repo bài nộp](https://github.com/NTD-DUONG/K5-L3A-DAY06-NguyenThuyDuong-2A202603388-DataIngestion).

## Cài môi trường

Các lệnh dưới đây chạy từ thư mục gốc repo với Python 3.13. Môi trường thực đo dùng Python 3.13.2 trên Windows. Cần mạng khi cài thư viện và tải model lần đầu.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lab.txt
.\.venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', revision='e8f8c211226b894fcb81acc59f3b34ba3efd5f42')"
```

Nếu `.venv` đã ở thư mục cha như lúc làm bài, dùng `..\.venv\Scripts\python.exe` thay cho `.\.venv\Scripts\python.exe`.

## Kiểm tra bài đã lưu

```powershell
.\.venv\Scripts\python.exe scripts/validate_submission.py
.\.venv\Scripts\python.exe scripts/summarize_audits.py
```

Lệnh đầu đối chiếu corpus, đơn vị nguồn, evidence, trace, chỉ số và cấu hình đã chọn. Lệnh thứ hai tổng hợp các nhãn có tên người chấm, lý do và xác nhận. Kết quả bài nộp đã có đủ 30 nhãn coherence, 15 grounding và 45 metadata được Nguyễn Thùy Dương xác nhận. Hồ sơ nằm trong `results/audit/student_confirmation.json`.

## Nguồn văn bản và cách xử lý

`data/manifest.json` liệt kê bảy nguồn Wikipedia tiếng Việt, snapshot, giấy phép văn bản, ghi công, ngày truy cập và 30 đơn vị. Bản MHTML chỉ chứa văn bản được nộp ở `data/text_sources/`. Quy trình đóng gói đã bỏ ảnh, CSS và nội dung thực thi. Log nguồn gốc và SHA-256 được lưu ở `data/processing_logs/text_source_packaging.json`.

Có thể kiểm tra lại một nguồn bằng lệnh sau.

```powershell
.\.venv\Scripts\python.exe scripts/extract_html.py data/text_sources/tranh_dong_ho.mhtml tranh_dong_ho.txt --check
```

Để tạo lại văn bản, chạy lệnh trên và bỏ tùy chọn `--check`. Làm tương tự theo `raw_path` và `processed_path` trong manifest cho các nguồn còn lại. Muốn lấy lại trang gốc, mở `snapshot_url` của nguồn trong trình duyệt và lưu MHTML. Các MHTML đầy đủ đã dùng trong quá trình làm bài được giữ tại máy trong `data/raw/`. Lệnh `python scripts/prepare_text_sources.py` dùng những bản local này để đóng gói lại nguồn văn bản.

Văn bản được đọc bằng email parser và BeautifulSoup, giải mã UTF-8, chuẩn hóa NFC và khoảng trắng. Giữ tiêu đề/đoạn và thẻ dt/dd chứa thơ. Phần lọc Khắc gỗ được ghi ở `data/processing_logs/khac_go_filter.json`.

## Chia đơn vị và chunk

```powershell
.\.venv\Scripts\python.exe scripts/build_source_units.py
.\.venv\Scripts\python.exe scripts/build_chunks.py
```

Mỗi đơn vị nguồn có ít nhất 1.500 ký tự, ID và ranh giới truy vết. Cấu hình A dùng cửa sổ 500 ký tự, overlap 50. B/C gom theo đoạn tối đa 1.000 ký tự và chia đoạn quá dài theo câu/từ. Artifact trong `artifacts/chunks/` có 131 chunk A và 71 chunk B/C. C dùng cùng chunk, vector và metadata với B. Các file JSON/JSONL được Git giữ nguyên byte để các hash kiểm chứng hoạt động trên nhiều hệ điều hành.

## Tái lập embedding và benchmark

Lệnh dưới đây tạo một lần chạy riêng trong `.runtime/reproduce1/`. Chọn một tên thư mục mới cho lần tái lập tiếp theo.

```powershell
.\.venv\Scripts\python.exe scripts/ingest_vectors.py --results-dir .runtime/reproduce1/results --database-dir .runtime/reproduce1/chroma
.\.venv\Scripts\python.exe scripts/evaluate_dev.py --results-dir .runtime/reproduce1/results
.\.venv\Scripts\python.exe scripts/evaluate_test.py --results-dir .runtime/reproduce1/results
```

Model local có 384 chiều, giới hạn 128 token gồm token đặc biệt. Adapter chia văn bản thành các cửa sổ tối đa 126 token nội dung, tạo embedding mỗi cửa sổ, gộp theo trọng số số token rồi chuẩn hóa L2. Document và query dùng cùng cách xử lý, cùng revision, cùng seed 0 và chạy CPU. Tổng token cửa sổ được đối chiếu với token nguồn.

Chroma PersistentClient dùng cosine và HNSW với ef_search=100. B/C tái sử dụng cùng vector. Upsert dùng ID ổn định và sync xóa ID đã lỗi thời trong snapshot mới. Đã kiểm tra nạp lại, mở database bằng tiến trình mới, vector và metadata. Chi phí API bằng 0. Chi phí điện, hardware và tải model chưa được đo.

Dev gồm 15 câu. Quy tắc chọn cấu hình ưu tiên Evidence Hit@3, rồi Hit@1, ít chunk, cuối cùng A/B/C. C được chọn trước khi chạy 5 câu test. Bộ câu hỏi, corpus và cấu hình có hash kiểm chứng. Khi chỉnh corpus hoặc cấu hình dựa trên test đã công bố, phải ghi nhận lần chạy mới và đánh giá giới hạn của việc đã biết test.

## Kết quả và audit

Kết quả tự động và trace gốc nằm trong `results/dev/` và `results/test/`. Kết quả sau khi chấp nhận evidence tương đương q16 nằm trong `results/audit/confirmed_test/`. Test sau review có Hit@1/Hit@3 lần lượt là A 2/5 và 2/5, B 1/5 và 2/5, C 1/5 và 3/5.

Phiếu đọc từng mẫu nằm trong `results/audit/CHAM_DOC_TUNG_MAU.md`. Các packet coherence/grounding/metadata.jsonl chứa nhãn, lý do, reviewer và phương thức xác nhận. Kết quả tổng hợp nằm trong `HUMAN_SUMMARY.md` và `human_summary.json`. Người chấm Nguyễn Thùy Dương đã xác nhận bản nhãn do trợ lý hỗ trợ soạn. Báo cáo ghi phương pháp và nguy cơ thiên lệch khi cùng công cụ tham gia tạo gold và đánh giá.

Mẫu coherence gồm 10 vị trí có quy tắc chọn được ghi trước khi gán điểm coherence và sau khi xem kết quả retrieval. Mẫu tập trung giấy dó/tổng quan. Bộ test có 5 câu. Các giới hạn này được nêu trong báo cáo.

## Báo cáo và lệnh thống nhất

Báo cáo cá nhân nằm trong `report/individual/2A202603388_NguyenThuyDuong.md`. Nhật ký thí nghiệm ở `artifacts/experiment_log.csv` ghi tham số, giả thuyết mô tả hồi cứu và số liệu thực đo. `python scripts/build_report.py` tạo lại hai file này từ artifact.

Từ thư mục repo, `python -m starter.src.run --stage check` chạy kiểm tra. Các stage có sẵn gồm units, chunks, ingest, dev, test, prepare-audit, audit-status và draft-report. Trong `starter/`, dùng `python -m src.run --stage check`. Pipeline hiện tại dùng Chroma và MHTML. Các khung PgVectorStore/load_pdf được cung cấp cùng đề bài vẫn nằm trong starter.

## Lỗi phát triển đã xử lý

- Transformers đang cài thiếu `BertConfig._commit_hash`. Adapter lấy revision từ tên thư mục snapshot cache.
- Tokenizer backend đang cài thiếu `prepare_for_model`. Adapter dùng overflow windows và kiểm tra đủ token.

Chi tiết phiên bản model, thư viện, thời điểm và thời gian đo nằm trong `results/ingestion/summary.json`. Các kết quả tính điểm được lưu từ lần chạy hoàn tất.
