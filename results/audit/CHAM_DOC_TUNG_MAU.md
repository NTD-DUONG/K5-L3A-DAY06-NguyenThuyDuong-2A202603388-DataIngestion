# Phiếu chấm bằng cách đọc từng mẫu

**Người chấm: Nguyễn Thùy Dương.**

**Phương pháp:** đọc nội dung từng chunk và top-3, đối chiếu đoạn nguồn, áp dụng thang điểm trong GUIDE.md và ghi lý do cụ thể. Không lấy Hit@3 tự động làm điểm grounding/coherence. **Trạng thái:** Nguyễn Thùy Dương đã xác nhận phiếu chấm qua hội thoại. Nguồn gốc nhãn và công cụ sử dụng được khai báo trong báo cáo cá nhân; không coi đây là chấm mù độc lập.

## 1. Grounding — đọc đủ top-3 của từng câu test

0 = không có bằng chứng trả lời; 1 = có nhưng thiếu điều kiện/ngữ cảnh; 2 = đủ để trả lời và truy nguồn.

| Câu | A | B | C | Nhận xét sau khi đọc |
|---|---:|---:|---:|---|
| q16: Có tô màu ngay sau in đen ở làng Sình không? | 2 | 2 | 2 | Top-1 cả ba có câu “Bản in đen chờ cho khô thì đem tô màu.” Câu tiếp theo nêu rõ tranh làng Sình. Dù nguồn là bài tổng quan thay vì bài riêng, bằng chứng đủ điều kiện phải chờ khô. Chấp nhận nguồn tương đương hoi_hoa_dan_gian_u008. |
| q17: Bản khắc làng Sình dùng gỗ gì? | 0 | 0 | 2 | A/B trả về khắc gỗ tổng quát, lịch sử châu Âu và hoàng dương, không xác định gỗ mít cho làng Sình. Top-2 của C ghi “Bản khắc của tranh được làm từ gỗ mít”, nằm trong tranh_lang_sinh_u002; đủ đáp án và truy nguồn. |
| q18: Bút vẽ làng Sình làm từ cây gì? | 0 | 0 | 0 | A có đoạn làng Sình nhưng chỉ nói tô màu và bố cục; đoạn dụng cụ khác nói dao/đục. B/C có đoạn Đông Hồ, Hàng Trống/Kim Hoàng và tô màu làng Sình. Không chunk nào trong top-3 nêu cây dứa. Không tính có tên dòng tranh là có bằng chứng. |
| q19: Vì sao gỗ thông không thích hợp? | 1 | 0 | 0 | Top-3 của A có mảnh “(Pinus) vì gỗ này có nhiều mấu và nhựa” nhưng mất chủ thể “gỗ thông” và điều kiện không thích hợp. Đọc một phần có thể suy đoán, chưa đủ bằng chứng đầy đủ trong một chunk. B/C chỉ có vân gỗ, khắc gỗ tổng quát và hoàng dương, không có nguyên nhân cần tìm. |
| q20: Sau mỗi lần in cần làm gì? | 2 | 2 | 2 | A top-1, B/C top-2 có nguyên câu “Sau mỗi lần in phải quét mực lại cho bản in khắc gỗ.” Đủ hành động, thời điểm và đối tượng, truy về khac_go_u002. |

Tổng hợp từ các nhãn đã đọc ở trên:

- A: mức 0/1/2 = 2/1/2; trung bình 1,0/2.
- B: mức 0/1/2 = 3/0/2; trung bình 0,8/2.
- C: mức 0/1/2 = 2/0/3; trung bình 1,2/2.

## 2. Coherence — đọc chunk bao phủ cùng 10 vị trí

Mỗi hàng có một chunk của A, một chunk của B và chunk C giống hệt B. Vị trí nguồn và nội dung đầy đủ lưu trong coherence.jsonl. Điểm 1 nghĩa là còn hiểu một phần nhưng thiếu ngữ cảnh; không tự cho 0 chỉ vì có một từ bị cắt nếu nội dung giữa chunk vẫn hiểu được.

| Mẫu | Unit nguồn | A | B | C | Nhận xét cụ thể |
|---|---|---:|---:|---:|---|
| coh01 | giay_do_u001 | 1 | 2 | 2 | A bắt đầu “nh Thăng Long” và kết thúc “đan bằng tre để”, cắt hai đầu quy trình. B/C bắt đầu câu đầy đủ về làng nghề và kết thúc trọn câu về người đan liềm, vẫn đọc được chuỗi công đoạn. |
| coh02 | giay_do_u002 | 1 | 2 | 2 | A bắt đầu “iếu thờ”, kết thúc “mà mịn”, thiếu hai đầu. B/C giải thích cấu trúc, độ bền rồi tới làng nghề bằng câu đầy đủ, người đọc xác định được giấy dó. |
| coh03 | giay_do_u003 | 1 | 1 | 1 | A mất đầu câu, cuối dừng “Nguyên liệu chủ”. B/C giữ các đoạn ứng dụng/độ bền nhưng treo hai tiêu đề “Lịch sử sản xuất giấy dó”, “Cây dó giấy” ở cuối, chưa có nội dung cho ý mới. Không chấm tối đa chỉ vì chia theo đoạn. |
| coh04 | hoi_hoa_dan_gian_u001 | 1 | 2 | 2 | A mở bằng “. Sở dĩ chúng”, không có tiền đề, cuối là “Tời thời kỳ”. B/C có định nghĩa, phân loại và lịch sử, giữ đầy đủ câu và chủ thể. |
| coh05 | hoi_hoa_dan_gian_u002 | 1 | 2 | 2 | A mất phần “Tranh dân gian”, cuối cắt “ngày”, nên thiếu ngữ cảnh. B/C giữ giải thích nét riêng và tạo hình hoàn chỉnh. Tiêu đề cuối giới thiệu mục tiếp theo nhưng ý chính đã hoàn chỉnh. |
| coh06 | hoi_hoa_dan_gian_u003 | 1 | 2 | 2 | A bắt đầu giữa “loại giấy”, cuối giữa “tranh”. B/C nêu rõ vẽ trực tiếp, giấy dó, giấy điệp và đặc tính, đọc được chủ thể và các câu trọn ý. |
| coh07 | hoi_hoa_dan_gian_u004 | 1 | 2 | 2 | A bắt đầu giữa câu “chặt chẽ”, cuối cắt “trống”. B/C có tiêu đề, quan niệm tạo hình, phạm vi đề tài và ví dụ truyện Nôm đủ ngữ cảnh. |
| coh08 | hoi_hoa_dan_gian_u005 | 1 | 2 | 2 | A cắt từ “ngày” ở đầu và câu tổng kết ở cuối, nhưng đoạn Đám cưới chuột còn hiểu. B/C giữ ý nghĩa tranh gà cùng giải thích Đám cưới chuột, không mất điều kiện chính. |
| coh09 | hoi_hoa_dan_gian_u006 | 1 | 1 | 1 | A bắt đầu giữa “nhanh”, thiếu câu mở. B/C đọc được phần phân loại và danh sách dòng tranh, nhưng kết thúc bằng mục “Dòng tranh dân gian Đông Hồ” chưa có nội dung; còn cần chunk tiếp. |
| coh10 | hoi_hoa_dan_gian_u007 | 1 | 1 | 1 | A mất đầu “nông thôn” và cuối danh sách tác phẩm. B/C mở bằng “Dòng tranh này” phải nối ngữ cảnh trước; dù đoạn sau xác định Đông Hồ, cuối lại treo tiêu đề Hàng Trống. |

Kết quả: A 1,0/2; B 1,7/2; C 1,7/2, mỗi cấu hình 10 mẫu. Mẫu tập trung giấy dó/tổng quan; không suy rộng rằng mọi chunk B/C đều mạch lạc. Quy tắc chọn mẫu được ghi trước điểm coherence nhưng sau khi xem kết quả retrieval.

## 3. Metadata — đối chiếu cả 45 bản ghi

Đọc source, unit/page, document_id, nhãn dòng tranh và đầu/cuối nội dung của từng bản ghi; đối chiếu snapshot/tiêu đề trong MHTML và văn bản nguồn theo offsets. Chi tiết 45 bản ghi kèm nguyên metadata nằm trong metadata.jsonl. Bảng dưới ghi ba kết luận tương ứng top-1/top-2/top-3 cho mỗi câu, không chỉ kiểm tra đủ tên trường.

| Cấu hình | Câu | Top-1 | Top-2 | Top-3 | Đối chiếu nguồn và phạm vi |
|---|---|---|---|---|---|
| A | q16 | Đúng | Đúng | Đúng | Hai chunk thuộc bài tổng quan, nhãn general; chunk còn lại Kim Hoàng, nhãn kim_hoang. Nói về làng Sình trong bài tổng quan không làm nhãn general sai. |
| A | q17 | Đúng | Đúng | Đúng | Cả ba thuộc Khắc gỗ, lần lượt u001/u005/u004, nhãn general. Metadata đúng nhưng cả ba không đáp ứng phạm vi làng Sình. |
| A | q18 | Đúng | Đúng | Đúng | Tổng quan u008, Khắc gỗ u003, Kim Hoàng u002; nội dung khớp nguồn. Không có câu trả lời không đồng nghĩa metadata sai. |
| A | q19 | Đúng | Đúng | Đúng | Khắc gỗ u001/u002/u002; offsets của chunk thứ ba bắt đầu ở giữa câu về Pinus. Metadata truy được mảnh câu dù chunk thiếu ngữ cảnh. |
| A | q20 | Đúng | Đúng | Đúng | Khắc gỗ u002/u003 và Hàng Trống u002; source/nhãn lần lượt general/general/hang_trong, không bị gán theo câu hỏi. |
| B | q16 | Đúng | Đúng | Đúng | Hai chunk tổng quan u008 và một chunk Kim Hoàng u002; snapshot và nhãn phản ánh tài liệu chứa nội dung. |
| B | q17 | Đúng | Đúng | Đúng | Khắc gỗ u001/u007/u005, nhãn general. Thông tin nguồn đúng, nhưng không tuân thủ filter làng Sình; B không bật filter theo thiết kế. |
| B | q18 | Đúng | Đúng | Đúng | Cả ba thuộc bài tổng quan, u006/u008/u008; nhãn general vẫn đúng dù nhắc nhiều dòng tranh. |
| B | q19 | Đúng | Đúng | Đúng | Khắc gỗ u002/u001/u007; nội dung về vân gỗ, khái niệm và Bewick đúng với các vị trí này. |
| B | q20 | Đúng | Đúng | Đúng | Khắc gỗ u001/u002/u001; tách riêng phần chế tạo, quét lại mực và ép giấy, offsets khớp nội dung. |
| C | q16 | Đúng | Đúng | Đúng | Giống B vì câu không cung cấp filter; tổng quan/tổng quan/Kim Hoàng. |
| C | q17 | Đúng | Đúng | Đúng | Cả ba đúng Tranh làng Sình, u001/u002/u002, nhãn lang_sinh. Tất cả tuân thủ filter và top-2 có gỗ mít. |
| C | q18 | Đúng | Đúng | Đúng | Giống B: tổng quan u006/u008/u008, nhãn general. Không tự thêm filter từ gold để sửa lỗi truy xuất. |
| C | q19 | Đúng | Đúng | Đúng | Giống B: Khắc gỗ u002/u001/u007, source và offset đúng. |
| C | q20 | Đúng | Đúng | Đúng | Giống B: Khắc gỗ u001/u002/u001, evidence cần tìm nằm ở top-2. |

Đủ và đúng theo schema/phạm vi đã khai báo: A 15/15, B 15/15, C 15/15. Không phát hiện lỗi source/page/nhãn trong mẫu. Đây không phải khẳng định mọi thông tin trong Wikipedia là đúng ngoài đời.

Filter test chỉ có q17: A 0/1, B 0/1, C 1/1. Các câu không yêu cầu filter là N/A ở mức câu, không tự tính 100%.

## 4. Quyết định về bằng chứng tương đương

Chấp nhận q16 top-1 ở cả ba cấu hình vì giữ đủ điều kiện chờ khô và có văn cảnh làng Sình. Không chấp nhận q19 của A thành hit đầy đủ vì một mảnh câu thiếu chủ thể không đủ evidence trong một chunk.

| Cấu hình | Hit@1 test sau đọc evidence | Hit@3 test sau đọc evidence |
|---|---:|---:|
| A | 2/5 | 2/5 |
| B | 1/5 | 2/5 |
| C | 1/5 | 3/5 |

Giữ riêng chỉ số nguyên văn tự động trong results/test. Không đổi cấu hình, câu hỏi hay lựa chọn C để tăng điểm. Các nhãn được trợ lý hỗ trợ soạn rồi Nguyễn Thùy Dương xác nhận; hồ sơ xác nhận ở student_confirmation.json. Không tuyên bố học viên chấm độc lập từ đầu.
