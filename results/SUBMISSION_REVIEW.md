# Rà soát bài trước nộp — 14/11/2026

Phiếu này ghi nhận phát hiện trong lượt kiểm tra ban đầu và kết quả khắc phục sau đó.

## Kết quả khắc phục

- Đã tạo bảy bản MHTML chỉ chứa văn bản trong data/text_sources, cập nhật manifest và loại MHTML đầy đủ khỏi danh sách file Git sẽ nộp. Trích xuất lại cả bảy bản khớp 52.822 ký tự đã chốt.
- Đã chốt báo cáo thành report/individual/2A202603388_NguyenThuyDuong.md và cập nhật các liên kết.
- Đã cập nhật README, PIPELINE và thông tin học viên. Repo được GitHub xác nhận công khai và tài khoản kết nối có quyền push.
- Phiên bản phát hành dùng tag submission-day06. Commit có thể tra qua tag trong STUDENT.md.
- Đã bổ sung thư mục kết quả/database riêng cho lần tái lập. Quy trình được chạy lại để đối chiếu với số liệu bài nộp.

## Các phát hiện ban đầu

## Các việc cần xử lý trước nộp

1. **Giấy phép dữ liệu gốc:** cả 7 file MHTML trong data/raw chứa ảnh SVG/PNG/JPEG/WebP/GIF và CSS. Manifest chỉ khai báo quyền văn bản Wikipedia; chưa kiểm tra quyền tái phân phối từng ảnh. Ghi “không sử dụng hình ảnh” trong pipeline không loại ảnh khỏi file MHTML sẽ được chia sẻ. Nên cung cấp bản nguồn chỉ chứa văn bản/HTML đã bỏ tài nguyên ảnh, hoặc chỉ nộp văn bản được phép kèm snapshot và hướng dẫn lấy lại MHTML, hoặc kiểm tra/ghi công từng tài nguyên trước khi nộp MHTML đầy đủ. Không tự coi giấy phép văn bản áp dụng cho tất cả ảnh.
2. **Git và thông tin nộp:** mã, corpus, benchmark và kết quả còn modified/untracked; chưa được đưa vào commit hiện tại. STUDENT.md thiếu Repo bài nộp và Commit chốt bài. Origin đã trỏ tới https://github.com/NTD-DUONG/K5-L3A-DAY06-NguyenThuyDuong-2A202603388-DataIngestion, nhưng chưa xác minh quyền truy cập của người chấm hoặc nội dung remote. Không commit/push trong lượt kiểm tra này.
3. **Tên báo cáo:** hiện là report/individual/BAO*CAO_NHAP.md. SUBMISSION.md yêu cầu report/individual/<MSSV>*<HoTen>.md; cần chốt thành 2A202603388_NguyenThuyDuong.md và cập nhật các liên kết/builder liên quan.
4. **Hướng dẫn còn trạng thái cũ:** PIPELINE.md có đoạn “Chưa hoàn tất review” và “các trường human để trống” dù phần đầu đã ghi nhận xác nhận. README còn nhắc thiếu MSSV/lớp dù đã điền. Cần thống nhất trạng thái để người chấm không nhầm.

## Đối chiếu yêu cầu và kết quả kiểm tra

| Mục               | Kết quả                                                                                                                |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Corpus            | 7 nguồn, 30 đơn vị web, 52.822 ký tự; min/max 1.511/2.943 ký tự mỗi đơn vị; ID và ranh giới khớp nguồn                 |
| Manifest          | Có nguồn, snapshot/version, giấy phép văn bản, ngày truy cập, số ký tự, danh sách unit và đường dẫn                    |
| Chuẩn hóa         | Có script đọc MHTML, UTF-8, Unicode NFC, lọc giao diện và nội dung lệch phạm vi; có log lọc Khắc gỗ                    |
| Ba chiến lược     | A 131 chunk; B/C 71 chunk; B/C cùng ID, nội dung và vector, chỉ đổi filter                                             |
| Embedding/store   | Embedding thật 384 chiều; Chroma lưu bền vững, cosine, filter; chuẩn hóa L2; không thấy vector không hữu hạn           |
| Nạp lại           | Có minh chứng nạp lại không tăng số bản ghi và mở lại bằng tiến trình mới                                              |
| Benchmark         | 20 câu, 15 dev/5 test, evidence khớp unit, 3 câu filter gồm 1 test                                                     |
| Dev/test          | 60 trace; mỗi trace có đủ 3 hit cùng score, text, metadata; chỉ số tính lại khớp artifact                              |
| Holdout           | C được chọn bằng dev và hash cố định trước test; không đổi cấu hình khi review q16                                     |
| Audit             | Có 30 coherence, 15 grounding, 45 metadata cùng lý do/tên người chấm; học viên đã xác nhận bản nhãn trợ lý hỗ trợ soạn |
| Năm khía cạnh     | Báo cáo có retrieval, coherence, metadata, grounding, tác động chiến lược và các ví dụ lỗi/giới hạn                    |
| Môi trường        | pip check không phát hiện dependencies xung đột; compileall các script/src thành công                                  |
| Tái tạo           | Tạo lại source_units và A/B/C chunk trong thư mục cô lập, kết quả khớp hoàn toàn artifact gốc                          |
| Liên kết tài liệu | Các Markdown link tương đối trong README, PIPELINE, báo cáo hiện đều có đích tồn tại                                   |
| Secret            | Quét mẫu phổ biến không phát hiện API key/token; đây không phải chứng minh không có mọi loại secret                    |

Chưa thử cài hoàn toàn từ đầu trong một môi trường mới; kiểm tra tái tạo dùng môi trường hiện có. Không chạy lại benchmark hoặc tinh chỉnh bằng test trong lượt rà soát này.

## Kết quả dùng trong báo cáo

| Cấu hình | Dev Hit@1 | Dev Hit@3 | Test tự động Hit@1/Hit@3 | Test sau review Hit@1/Hit@3 |
| -------- | --------: | --------: | ------------------------ | --------------------------- |
| A        |      6/15 |      9/15 | 1/5; 1/5                 | 2/5; 2/5                    |
| B        |      9/15 |     10/15 | 0/5; 1/5                 | 1/5; 2/5                    |
| C        |     10/15 |     11/15 | 0/5; 2/5                 | 1/5; 3/5                    |

Số sau review chấp nhận evidence tương đương q16, áp dụng cùng tiêu chí cho cả ba cấu hình và lưu tách khỏi số tự động. Coherence A/B/C = 1,0/1,7/1,7 trên 2; grounding = 1,0/0,8/1,2 trên 2; metadata 15/15 mỗi cấu hình; filter test 0/1, 0/1, 1/1.

## Giới hạn ảnh hưởng việc chấm

- Test chỉ 5 câu; Hit@3 thấp không tự làm bài không đạt vì rubric chấm minh chứng/phân tích.
- Một số nội dung tổng quan nhắc lại nguồn chuyên biệt; kiểm tra trùng chính xác không phải kiểm tra gần trùng/ngữ nghĩa đầy đủ. Corpus chỉ vừa đủ 30 đơn vị, nên phải đếm lại nếu loại thêm nội dung.
- Audit có công cụ hỗ trợ và học viên xác nhận, không chấm mù/độc lập. Cần giữ phương pháp và nguy cơ thiên lệch theo GUIDE/RULES; chỉ bản ghi xác nhận không chứng minh năng lực giải thích bài của học viên.
- Coherence thiên về giấy dó/tổng quan; token-window pooling tùy chỉnh; thời gian chỉ một lần đo, C tái dùng embedding B. Các giới hạn này đã được báo cáo.
- TODO trong starter/src/store.py và ingestion.py là khung PostgreSQL/PDF không được pipeline Chroma/MHTML hiện tại sử dụng; không phải bằng chứng pipeline đang dùng chưa hoàn thiện, nhưng nên ghi rõ để tránh nhầm.

Không thể cam kết điểm số thay giảng viên. Sau khi xử lý các mục trước nộp, bài có bộ minh chứng phù hợp với phần lớn yêu cầu của lab.
