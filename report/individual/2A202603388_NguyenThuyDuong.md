# Báo cáo cá nhân — Day 6

- Họ và tên: Nguyễn Thùy Dương
- MSSV: 2A202603388
- Lớp: L3A
- Repo bài nộp: https://github.com/NTD-DUONG/K5-L3A-DAY06-NguyenThuyDuong-2A202603388-DataIngestion
- Phiên bản bài nộp: `submission-day06-v2`

## Dữ liệu và pipeline

- **Chủ đề, nguồn và quy tắc tính trang.** Tôi chọn chủ đề **Tranh Đông Hồ và hội họa dân gian Việt Nam**, gồm bảy tài liệu tiếng Việt về Đông Hồ, hội họa dân gian, giấy dó, Hàng Trống, Kim Hoàng, làng Sình và khắc gỗ. Corpus có **52,822 ký tự sau chuẩn hóa**, chia thành **30 đơn vị nguồn**, mỗi đơn vị tối thiểu 1.500 ký tự. Các đơn vị được chia tuần tự trong từng tài liệu, ưu tiên kết thúc ở câu hoặc đoạn và gộp phần đuôi ngắn vào đơn vị trước. Mỗi đơn vị có ID, vị trí bắt đầu/kết thúc và số ký tự. Nguồn được truy cập ngày 13/11/2026, văn bản theo CC BY-SA 4.0 và điều khoản bổ sung ở từng trang. Manifest ghi URL, snapshot, giấy phép, ghi công và danh sách đơn vị trong `data/manifest.json`. Bản MHTML chỉ chứa văn bản nằm trong `data/text_sources/`.

- **Chuẩn hóa, lỗi và giới hạn.** Tôi đọc MHTML bằng email parser, giải mã UTF-8 và dùng BeautifulSoup lấy nội dung chính. Các bước xử lý gồm chuẩn hóa Unicode NFC, khoảng trắng, bỏ giao diện, ảnh, bảng, phần tham khảo và liên kết ngoài. Thẻ dt/dd được giữ để lấy các đoạn thơ. Với bài Khắc gỗ, tôi bỏ nội dung in trên đồ vật, quảng cáo và khắc bút chì vì lệch phạm vi. Log nằm trong `data/processing_logs/`. Đã đối chiếu văn bản trích xuất với bản nguồn nộp và kiểm tra ranh giới của 30 đơn vị. Nguồn tổng quan có một số thông tin gần trùng với bài chuyên biệt, vì vậy corpus chưa được loại trùng ngữ nghĩa toàn diện. Nội dung Wikipedia cũng có những phát biểu cần thận trọng về độ chính xác.

- **Embedding, vector store, lệnh chạy và chi phí.** Tôi dùng model local `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, tạo vector **384 chiều** trên CPU. Phiên bản thư viện gồm sentence-transformers 6.3.0, chromadb 1.5.9, torch 2.15.0, transformers 5.23.0, numpy 2.5.4. Model có giới hạn 128 token, gồm token đặc biệt. Văn bản dài được xử lý thành các cửa sổ tối đa 126 token nội dung, tạo vector từng cửa sổ, gộp trung bình theo số token và chuẩn hóa L2. Document/query và cả ba cấu hình dùng cùng cách xử lý. Chroma PersistentClient lưu dữ liệu ở `.runtime/chroma`, dùng cosine và HNSW approximate search, ef_search=100. Đã kiểm tra nạp lại cùng snapshot giữ đúng số bản ghi, mở database bằng tiến trình mới và đối chiếu nội dung/metadata. Khi tài liệu thay đổi, tạo lại đơn vị và chunk rồi sync để xóa các ID đã lỗi thời. Chi phí API là **0**, chưa tính điện, hardware và thời gian tải model.

Các lệnh tái lập chạy từ thư mục repo sau khi cài `requirements-lab.txt` và tải model. Hướng dẫn đầy đủ nằm trong `PIPELINE.md`.

```powershell
python scripts/build_source_units.py
python scripts/build_chunks.py
python scripts/ingest_vectors.py --results-dir .runtime/reproduce1/results --database-dir .runtime/reproduce1/chroma
python scripts/evaluate_dev.py --results-dir .runtime/reproduce1/results
python scripts/evaluate_test.py --results-dir .runtime/reproduce1/results
python scripts/validate_submission.py
```

- **Metadata và trường lọc.** Mỗi chunk có `document_id`, `source`, `page` là ID đơn vị nguồn, offsets và `snapshot_url`. Tôi bổ sung `painting_tradition` kiểu string, lấy theo phạm vi chính từ tiêu đề tài liệu. Các giá trị gồm `dong_ho`, `hang_trong`, `kim_hoang`, `lang_sinh` và `general`. Quy tắc được ghi trong `benchmark/metadata_scopes.json`. Source/page/offset giúp truy ngược về tài liệu, còn trường dòng tranh giúp giới hạn phạm vi khi câu hỏi có yêu cầu. Một hạn chế là bài tổng quan được gắn general dù có đoạn nói về một dòng tranh cụ thể, nên filter có thể loại bỏ bằng chứng liên quan.

## Cấu hình và benchmark

- **Cấu hình A/B/C.** A chia cố định 500 ký tự với overlap 50. B chia theo đoạn, ghép tối đa 1.000 ký tự và tách đoạn dài theo câu hoặc từ, overlap 0. C dùng đúng chunk, vector và metadata của B, chỉ bật filter khi câu hỏi cung cấp phạm vi. A/B tìm kiếm không filter. So sánh A–B phản ánh tổng thể kích thước, overlap và cách chia, còn B–C chỉ thay việc áp dụng filter. Cả ba dùng cùng corpus, model, cosine và top-3.

- **Bộ câu hỏi và kiểm chứng evidence.** Benchmark có 20 câu, chia trước thành **15 dev / 5 test**, gồm câu trực tiếp, diễn đạt lại và câu có điều kiện. q07, q10 thuộc dev và q17 thuộc test kiểm tra metadata filter. Mỗi câu có đáp án, nguồn, unit và evidence đã đối chiếu nguyên văn với corpus. Filter lấy từ phạm vi nêu trong câu hỏi. Bộ dev chủ yếu bao phủ giấy dó, tổng quan, Đông Hồ, Hàng Trống và Kim Hoàng. Test bao phủ làng Sình và kỹ thuật khắc gỗ. Do nguồn tổng quan nhắc lại nhiều dòng tranh, hai split vẫn có giao thoa chủ đề. Câu hỏi và gold nằm trong `benchmark/questions.json`, phương pháp chia và hash nằm trong `benchmark/protocol.json`.

- **Tiêu chí chọn chiến lược trước test.** Tôi ưu tiên Evidence Hit@3 trên dev, tiếp theo Hit@1, số chunk ít hơn và cuối cùng thứ tự A/B/C. Kết quả dev chọn **C**. Cấu hình, bộ câu hỏi, corpus và lựa chọn được cố định bằng hash trong `results/dev_selection.json` trước khi chạy test.

## Kết quả

Một hit yêu cầu một chunk chứa đủ evidence và truy được nguồn/unit hợp lệ, bao gồm bằng chứng tương đương được chấp nhận sau đọc đối chiếu. Bảng dưới dùng kết quả dev từ phép đối chiếu evidence nguyên văn và kết quả test sau rà soát top-3. Riêng q16 chấp nhận câu tương đương trong nguồn tổng quan. Tại test, số nguyên văn tự động ban đầu của A/B/C lần lượt là Hit@1 1/5, 0/5, 0/5 và Hit@3 1/5, 1/5, 2/5. Các trace và kết quả sau rà soát được lưu đầy đủ để đối chiếu.

Thời gian trong bảng là embedding cộng lần sync Chroma đầu tiên. Đây là một lần đo local. C tái dùng embedding của B nên cột thời gian ghi rõ phần lưu bổ sung.

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---|---|---|
| A | dev | 6/15 | 9/15 | 131 | 7.425 giây | 0 |
| B | dev | 9/15 | 10/15 | 71 | 5.013 giây | 0 |
| C | dev | 10/15 | 11/15 | 71 | Tái dùng B + 0.122 giây lưu | 0 |
| A | test | 2/5 | 2/5 | 131 | 7.425 giây | 0 |
| B | test | 1/5 | 2/5 | 71 | 5.013 giây | 0 |
| C | test | 1/5 | 3/5 | 71 | Tái dùng B + 0.122 giây lưu | 0 |

| Strategy | Coherence trung bình /2 (n) | Metadata đủ và đúng (n/N) | Filter tuân thủ (n/N hoặc N/A) | Grounding 0/1/2 (số câu) và trung bình /2 |
|---|---|---|---|---|
| A | 1.00 (n=10) | 15/15 | 0/1 | 2/1/2 câu, trung bình 1.00/2 |
| B | 1.70 (n=10) | 15/15 | 0/1 | 3/0/2 câu, trung bình 0.80/2 |
| C | 1.70 (n=10) | 15/15 | 1/1 | 2/0/3 câu, trung bình 1.20/2 |

**Đường dẫn trace, nhãn và cách chọn mẫu.** `results/dev/*_traces.jsonl` và `results/test/*_traces.jsonl` lưu câu hỏi, top-3 chunk, score, metadata và kết quả nguyên văn tự động. `results/audit/confirmed_test/` lưu kết quả sau rà soát evidence. Nhãn cùng lý do nằm trong `results/audit/coherence.jsonl`, `grounding.jsonl`, `metadata.jsonl` và phiếu `CHAM_DOC_TUNG_MAU.md`.

Coherence được chấm trên cùng 10 vị trí nguồn cho mỗi cấu hình. Tôi lấy 10 unit ID đầu theo thứ tự chữ, chọn vị trí ký tự 750 và dịch qua khoảng trắng, rồi lấy chunk bao phủ vị trí đó. Quy tắc chọn mẫu được ghi trước khi gán điểm coherence, sau khi đã xem kết quả retrieval. Mẫu tập trung giấy dó/tổng quan nên có thiên lệch phạm vi. Thang coherence là 0 khi đoạn bị cắt hoặc thiếu chủ thể đến mức không hiểu, 1 khi hiểu một phần và 2 khi tự hiểu được, giữ trọn ý.

Metadata được đối chiếu trên 5 câu test × top-3 của từng cấu hình, gồm source, page/unit, snapshot, offsets và trường dòng tranh. Mẫu không phát hiện lỗi metadata. q17 là câu test duy nhất có filter, A/B đạt 0/1 và C đạt 1/1 về tuân thủ phạm vi. Grounding được chấm cho top-3 của cả 5 câu test, mức 0 khi không có bằng chứng, 1 khi thiếu điều kiện/ngữ cảnh và 2 khi đủ để trả lời và truy nguồn. Phần đánh giá tập trung mức đầy đủ của bằng chứng truy xuất.

**Tài nguyên.** A có độ dài chunk min/median/max 98/500/500 ký tự, tổng 57.872 ký tự và 15.813 token nội dung. B/C có 69/805/1.000 ký tự, tổng 52.712 ký tự và 14.385 token. A có tổng lượng văn bản lớn hơn do overlap. Chi tiết thời gian, token và phiên bản nằm trong `artifacts/chunks/summary.json` và `results/ingestion/summary.json`.

## Phân tích và kết luận

- **So sánh A–B và B–C.** B tăng Evidence Hit@3 dev từ 9/15 lên 10/15 và giảm số chunk từ 131 xuống 71. Coherence tăng từ 1,00/2 lên 1,70/2 trong mẫu đã chọn. Tuy nhiên, trên test sau rà soát, A và B cùng đạt Hit@3 2/5, còn Hit@1 của A là 2/5 và B là 1/5. C dùng cùng vector B nhưng thêm filter, tăng Hit@3 dev lên 11/15 và test lên 3/5. Kết quả cho thấy lợi ích của filter trong corpus này khi có phạm vi câu hỏi rõ ràng.

- **Ví dụ lỗi q18.** Câu hỏi cần biết bút vẽ làng Sình làm từ cây gì, evidence ở `tranh_lang_sinh_u002` nêu cây dứa. Cả ba cấu hình trả về các đoạn về tranh và kỹ thuật tô màu, không truy xuất được chi tiết cần trả lời. Vì top-3 thiếu bằng chứng, grounding được chấm 0 cho cả ba.

- **Ví dụ lỗi q19.** Evidence ở `khac_go_u002` giải thích gỗ thông có nhiều mấu và nhựa. A trả về mảnh câu “(Pinus) vì gỗ này có nhiều mấu và nhựa” nhưng mất chủ thể và điều kiện không thích hợp, nên grounding là 1 và chưa đủ một hit đầy đủ. B/C trả về các đoạn về vân gỗ, hoàng dương và lịch sử khắc gỗ, nên grounding là 0. Trường hợp này thể hiện đồng thời lỗi ranh giới chunk và lỗi xếp hạng.

- **Trường hợp filter q17.** A/B lấy các đoạn khắc gỗ tổng quát. C giới hạn `painting_tradition=lang_sinh`, đưa đoạn “Bản khắc của tranh được làm từ gỗ mít” ở `tranh_lang_sinh_u002` vào top-2. Ba bản ghi của C đều tuân thủ filter. Đây là ví dụ tác động của việc lọc phạm vi khi giữ nguyên chunk và embedding của B.

- **Bằng chứng tương đương q16.** Top-1 của cả ba cấu hình có câu “Bản in đen chờ cho khô thì đem tô màu” trong `hoi_hoa_dan_gian_u008`, có văn cảnh làng Sình. Đoạn này đủ điều kiện để trả lời dù khác nguồn gold ưu tiên. Tôi chấp nhận bằng chứng tương đương, ghi lý do và bổ sung kết quả sau rà soát trong artifact.

- **Chiến lược chọn và điều kiện áp dụng.** Tôi chọn **C** theo kết quả dev đã cố định trước test. C phù hợp khi câu hỏi cung cấp dòng tranh và metadata đáng tin cậy. Với câu không có filter, C thực hiện như B. Chunk theo đoạn giúp giữ ngữ cảnh, nhưng một số ranh giới đơn vị nguồn vẫn cắt ý và một số chunk kết thúc ở tiêu đề chưa có nội dung. Filter theo phạm vi tài liệu cũng có thể loại bài tổng quan chứa evidence liên quan.

- **Hạn chế.** Corpus có thông tin gần trùng và chất lượng nguồn không đồng đều. Test chỉ có 5 câu nên mỗi câu làm thay đổi chỉ số 20 điểm phần trăm. Có một người chấm, nguy cơ thiên lệch khi đánh giá chính bài làm và khi đã xem kết quả retrieval. Mẫu coherence thiên về giấy dó/tổng quan. Cách gộp embedding nhiều cửa sổ là tùy chỉnh, chưa đối chiếu với model dài ngữ cảnh hơn. Thời gian chỉ được đo một lần trên máy local, C tái sử dụng vector B, chi phí chỉ ghi nhận API. Kết quả áp dụng trong phạm vi corpus và benchmark này.

- **Cải tiến khi làm lại.** Tôi sẽ tăng số câu test và phân bố theo tài liệu/chủ đề, chuẩn bị thêm nguồn ít trùng lặp, chọn mẫu coherence phủ đều các dòng tranh và kiểm tra nhãn bằng người chấm thứ hai. Tôi cũng sẽ thử model hỗ trợ ngữ cảnh dài và hybrid retrieval, chọn tham số trên dev rồi đánh giá bằng một tập test mới nếu đã dùng kết quả hiện tại để thiết kế lại.
