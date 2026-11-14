"""Assemble the individual report from measured artifacts and review records."""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def ratio(metric):
    return f"{metric['numerator']}/{metric['denominator']}"


def main():
    manifest = read("data/manifest.json")
    chunking = read("artifacts/chunks/summary.json")["strategies"]
    ingestion = read("results/ingestion/summary.json")
    dev = read("results/dev/summary.json")["strategies"]
    test = read("results/test/summary.json")["strategies"]
    selection = read("results/dev_selection.json")
    proposals = read("results/audit/ai_proposals.json")
    configs = read("configs/strategies.json")
    hypotheses = {
        "A": "Baseline cửa sổ ký tự có thể cắt mất ý dù có overlap.",
        "B": "Chia theo đoạn có thể giữ ngữ cảnh tốt hơn và giảm số chunk.",
        "C": "Filter theo phạm vi câu hỏi có thể giảm nhiễu so với B.",
    }
    # Machine-readable experiment artifact, preserving the lab CSV schema.
    with (ROOT / "artifacts/experiment_log.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["strategy", "chunking", "chunk_size", "overlap", "metadata", "filter", "vectorizer", "hypothesis", "dev_hit1", "dev_hit3", "test_hit1", "test_hit3", "notes"])
        writer.writeheader()
        for name in ["A", "B", "C"]:
            config = configs[name]
            writer.writerow({
                "strategy": name, "chunking": config["chunk_method"],
                "chunk_size": config.get("chunk_size_chars", config.get("max_chunk_size_chars")),
                "overlap": config["overlap_chars"],
                "metadata": "document_id;source;page;painting_tradition;offsets;snapshot_url",
                "filter": "painting_tradition when question supplies scope" if name == "C" else "none",
                "vectorizer": ingestion["model"]["model_name"], "hypothesis": hypotheses[name],
                "dev_hit1": ratio(dev[name]["hit_at_1"]), "dev_hit3": ratio(dev[name]["evidence_hit_at_3"]),
                "test_hit1": ratio(test[name]["hit_at_1"]), "test_hit3": ratio(test[name]["evidence_hit_at_3"]),
                "notes": "Hypothesis description recorded retrospectively. Metrics are automatic exact-evidence results. Confirmed equivalent-evidence review is in results/audit/confirmed_test/summary.json." + (" Reuse B embeddings." if name == "C" else ""),
            })

    lines = [
        "# Báo cáo cá nhân — Day 6", "",
        "**Trạng thái:** pipeline và benchmark đã chạy; chưa hoàn thành nhãn thủ công của học viên. Các đề xuất AI được tách riêng. Chưa xác nhận đây là bài nộp hoàn chỉnh.", "",
        "Họ tên **Nguyễn Thùy Dương**, MSSV **2A202603388**, lớp **L3A**.", "",
        "Repo bài nộp https://github.com/NTD-DUONG/K5-L3A-DAY06-NguyenThuyDuong-2A202603388-DataIngestion. Phiên bản chốt được gắn tag `submission-day06`.", "",
        "**Người chấm: Nguyễn Thùy Dương.** Trạng thái: chờ rà soát và xác nhận nhãn.", "",
        "## Dữ liệu và pipeline", "",
        f"Chủ đề {manifest['corpus_title']}. Bảy nguồn Wikipedia tiếng Việt được nộp dạng MHTML chỉ chứa văn bản trong data/text_sources. Ảnh, CSS và nội dung thực thi đã được loại khỏi bản nộp. Văn bản theo CC BY-SA 4.0 và điều khoản bổ sung ở nguồn. Ngày truy cập 13/11/2026. Manifest ghi URL, snapshot, giấy phép, ghi công, file và ID đơn vị. Đã trích xuất lại cả bảy bản chỉ chứa văn bản và đối chiếu khớp corpus đã chốt. Log đóng gói ở data/processing_logs/text_source_packaging.json.", "",
        "| Tài liệu | Ký tự chuẩn hóa | Đơn vị nguồn |", "|---|---:|---:|",
    ]
    for doc in manifest["documents"]:
        lines.append(f"| {doc['title']} | {doc['char_count']:,} | {len(doc['unit_ids'])} |")
    total = sum(doc["char_count"] for doc in manifest["documents"])
    lines += [
        f"| **Tổng** | **{total:,}** | **30** |", "",
        "Dữ liệu web không quy đổi thành 30 trang PDF. Chia tuần tự trong từng tài liệu, mỗi đơn vị ít nhất 1.500 ký tự; ưu tiên kết thúc ở câu/đoạn, gộp phần đuôi ngắn. ID và ranh giới start_char/end_char nằm trong data/source_units.jsonl. Đã kiểm tra khớp văn bản, không overlap, không thiếu ký tự và không có đơn vị trùng hoàn toàn. Chưa coi đây là kiểm tra loại trùng ngữ nghĩa toàn diện; nguồn tổng quan lặp lại một số thông tin của các bài chuyên biệt.", "",
        "Đọc MHTML bằng email parser, giải mã UTF-8, dùng BeautifulSoup lấy nội dung chính, chuẩn hóa Unicode NFC/khoảng trắng, bỏ giao diện, bảng/hình và phần tham khảo/liên kết. Bổ sung dt/dd để giữ đoạn thơ. Nguồn Khắc gỗ bỏ ứng dụng in trên đồ vật/quảng cáo và khắc bút chì; lý do ở data/processing_logs/khac_go_filter.json. Các phần lịch sử khắc gỗ quốc tế được giữ làm tài liệu nền, không coi là thông tin riêng của Đông Hồ.", "",
        "Nguồn Wikipedia có câu thiếu dẫn nguồn và một số cách diễn đạt/lịch sử cần thận trọng. Benchmark đánh giá truy xuất theo snapshot, không chứng minh mọi phát biểu trong Wikipedia đúng ngoài đời. Không tự sửa phát biểu nguồn để làm tăng điểm.", "",
        f"Embedding local CPU: `{ingestion['model']['model_name']}`, revision `{ingestion['model']['revision']}`, 384 chiều. Thư viện: " + "; ".join(f"{k} {v}" for k, v in ingestion["libraries"].items()) + ".", "",
        "Model giới hạn 128 token gồm token đặc biệt; dùng cửa sổ 126 token nội dung không overlap, model pooling từng cửa sổ, gộp trung bình theo số token và chuẩn hóa L2. Dùng cùng xử lý cho document/query và A/B/C, không prefix; đã kiểm tra không mất token. Đây là cách biểu diễn tùy chỉnh, chưa được so sánh với model dài ngữ cảnh hơn.", "",
        "Chroma PersistentClient ở .runtime/chroma, cosine, HNSW approximate search với ef_search=100. Có source, page/unit, document_id, offsets, snapshot_url và painting_tradition (string). Nhãn dòng tranh gán từ phạm vi chính trong tiêu đề tài liệu; tài liệu nền/tổng quan là general. Nguồn định nghĩa: benchmark/metadata_scopes.json.", "",
        "Upsert bằng ID ổn định; nạp lại giữ nguyên số vector. Nếu corpus thay đổi, tạo lại units/chunks trước khi sync; ID không còn trong snapshot sẽ bị xóa. Đã kiểm tra mở database bằng tiến trình mới, metadata/text khớp artifact, B/C vector giống nhau. Chưa có thí nghiệm thực tế thay tài liệu để đo cơ chế xóa chunk cũ. API cost = 0; chưa tính điện/hardware/tải model.", "",
        "## Cấu hình và benchmark", "",
        "| Cấu hình | Chia chunk | Filter |", "|---|---|---|",
        "| A | 500 ký tự, overlap 50 | Không |",
        "| B | Theo đoạn, tối đa 1.000 ký tự; chia đoạn dài theo câu/từ | Không |",
        "| C | Đúng chunk và vector B | Chỉ dùng khi câu hỏi cung cấp phạm vi |", "",
        "A–B so sánh tổng thể hai cấu hình chunking (bao gồm kích thước và overlap), không quy toàn bộ thay đổi cho riêng ranh giới đoạn. B–C chỉ khác filter. Các chunk không vượt ranh giới đơn vị nguồn; chính ranh giới đơn vị có thể cắt đoạn.", "",
        "20 câu được tạo trước truy xuất, 15 dev / 5 test. q07, q10 (dev) và q17 (test) có filter. Giá trị filter lấy từ phạm vi nêu trong câu hỏi, không từ đáp án/gold source. Evidence nguyên văn đã kiểm tra trong unit. Dev chủ yếu giấy dó/tổng quan/Đông Hồ/Hàng Trống/Kim Hoàng; test dành làng Sình và kỹ thuật khắc gỗ. Nguồn tổng quan vẫn làm giao thoa chủ đề giữa split.", "",
        "Tiêu chí chốt trước test: ưu tiên Evidence Hit@3 dev, rồi Hit@1 dev, rồi ít chunk, cuối cùng A/B/C. Chọn **C** bằng dev; hash và thời điểm cố định ở results/dev_selection.json. Không thay cấu hình sau khi xem test.", "",
        "## Kết quả truy xuất tự động", "",
        "Hit yêu cầu chunk thuộc nguồn/unit gold hợp lệ và chứa đủ evidence nguyên văn sau chuẩn hóa Unicode/khoảng trắng. Tính trên một chunk; ghép nhiều chunk không thay định nghĩa. Bằng chứng tương đương cần review; bảng này giữ nguyên kết quả tự động ban đầu.", "",
        "| Cấu hình | Split | Hit@1 | Evidence Hit@3 | Số chunk |", "|---|---|---:|---:|---:|",
    ]
    for split, reports in [("dev", dev), ("test", test)]:
        for name in ["A", "B", "C"]:
            lines.append(f"| {name} | {split} | {ratio(reports[name]['hit_at_1'])} | {ratio(reports[name]['evidence_hit_at_3'])} | {chunking[name]['chunk_count']} |")
    lines += ["", "| Cấu hình | Độ dài min/median/max (ký tự) | Tổng ký tự chunk | Token nội dung | Embedding (giây) | Sync Chroma (giây) |", "|---|---|---:|---:|---:|---:|"]
    for name in ["A", "B", "C"]:
        ch, ing = chunking[name], ingestion["strategies"][name]
        elapsed = "Tái dùng B" if name == "C" else f"{ing['embedding_seconds_this_run']:.3f}"
        lines.append(f"| {name} | {ch['min_chars']}/{ch['median_chars']}/{ch['max_chars']} | {ch['total_chunk_chars']} | {ing['embedding_stats']['content_tokens']} | {elapsed} | {ing['storage_sync_seconds']:.3f} |")
    lines += [
        "", "Thời gian là một lần đo cục bộ, không phải benchmark tốc độ lặp nhiều lần. C tái sử dụng embedding B nên không kết luận C nhanh hơn về embedding. Tổng token A lớn hơn do overlap. Chi phí API cả ba = 0.", "",
        "## Audit và năm khía cạnh", "",
        "1. **Retrieval:** kết quả thực đo ở bảng trên; trace đầy đủ tại results/dev và results/test. q16 có bằng chứng tương đương hợp lệ tiềm năng từ nguồn tổng quan, cần ghi nhận sau review.",
        "2. **Coherence:** đã chọn cùng 10 vị trí (10 unit ID đầu theo thứ tự chữ, ký tự 750 dịch qua whitespace) và lấy chunk bao phủ. Quy tắc ghi trước khi gán điểm coherence nhưng sau khi xem retrieval, không chấm mù. Mẫu thiên về giấy dó/tổng quan. 30 dòng trong results/audit/coherence.jsonl; nhãn học viên còn trống.",
        "3. **Metadata:** 45 bản ghi top-3 của test được kiểm tra máy với manifest/offset, đạt 15/15 mỗi cấu hình; chưa gọi là tỷ lệ đã audit thủ công. Filter test q17: A 0/1, B 0/1, C 1/1 theo kiểm tra máy. A/B không bật filter theo thiết kế. Metadata giúp truy vết và lọc; hạn chế general có thể loại bằng chứng liên quan khi lọc theo dòng tranh.",
        "4. **Grounding:** 15 dòng test top-3 đã chuẩn bị, thang 0/1/2, nhãn học viên còn trống. Đề xuất AI dựa trên đọc bằng chứng ở ai_proposals.json; không dùng Hit@3 thay grounding, không đánh giá câu trả lời LLM.",
        "5. **Data strategy impact:** B tăng Hit@3 dev từ 9/15 lên 10/15 và giảm 131 xuống 71 chunk; test tự động A/B cùng 1/5. C tăng dev lên 11/15 và test lên 2/5 nhờ phạm vi filter, nhưng không suy rộng ngoài corpus và mẫu nhỏ.", "",
        "### Đề xuất AI — chưa phải kết quả chấm của học viên", "",
        "| Cấu hình | Coherence AI đề xuất /2 | Grounding AI: số mức 0/1/2 | Grounding AI TB /2 | Trạng thái |", "|---|---:|---|---:|---|",
    ]
    for name in ["A", "B", "C"]:
        coh = [x["ai_proposed_score"] for x in proposals["coherence_proposals"] if x["strategy"] == name]
        gro = [x["ai_proposed_score"] for x in proposals["grounding_proposals"] if x["strategy"] == name]
        lines.append(f"| {name} | {sum(coh)/len(coh):.2f} (n={len(coh)}) | {gro.count(0)}/{gro.count(1)}/{gro.count(2)} | {sum(gro)/len(gro):.2f} | Chờ học viên đọc/chấm |")
    lines += [
        "", "AI đề xuất chấp nhận q16 top-1 của cả ba cấu hình: “Bản in đen chờ cho khô thì đem tô màu.” trong hoi_hoa_dan_gian_u008, văn cảnh xác định tranh làng Sình. Nếu được học viên xác nhận và không có sửa đổi review khác, test sẽ là A Hit@1 2/5 và Hit@3 2/5; B 1/5 và 2/5; C 1/5 và 3/5. Chưa dùng các số dự kiến này thay số tự động hoặc chọn lại cấu hình.", "",
        "## Phân tích lỗi và kết luận", "",
        "- **q17:** A/B trả về khắc gỗ tổng quát/châu Âu thay vì gỗ mít cho làng Sình. C có cùng vector B nhưng filter lang_sinh đưa evidence đúng vào top-2; đây là ví dụ tác động riêng của filter.",
        "- **q19:** A trả về mảnh câu ‘(Pinus) vì gỗ này có nhiều mấu và nhựa’ ở top-3 nhưng mất chủ thể gỗ thông/điều kiện không thích hợp. B/C lấy các đoạn về vân gỗ/hoàng dương, thiếu đáp án. Lỗi ranh giới và lỗi xếp hạng khác nhau; không tính partial evidence thành hit đầy đủ.",
        "- **q18:** cả ba không lấy được chi tiết bút vẽ làng Sình làm từ cây dứa. C không áp dụng filter vì câu này không cung cấp filter input trong benchmark; không thêm filter sau khi xem test.",
        "- **q16:** câu trả về có nghĩa đúng nhưng khác câu gold/nguồn gold, cho thấy giới hạn exact matching. Ghi nhận bằng review có lý do, không sửa ngầm nhãn hay query.", "",
        "Lựa chọn theo dev là C, phù hợp khi ngữ cảnh người dùng cung cấp dòng tranh và metadata đáng tin. Với câu không có filter, C giống B và vẫn mắc lỗi xếp hạng. Chunk dài giữ ngữ cảnh nhưng nhiều token/cửa sổ hơn trên mỗi chunk; chunk ngắn có thể mất điều kiện/chủ thể. Đánh giá hiện tại chưa đủ kết luận cấu hình tối ưu tổng quát.", "",
        "Giới hạn: dữ liệu Wikipedia và thông tin gần trùng; chỉ 5 test; gold AI hỗ trợ; chưa có người chấm độc lập; coherence chọn mẫu sau retrieval và thiên lệch phạm vi; metadata theo tài liệu, không theo mọi đoạn; token-window pooling tùy chỉnh; chưa đo nhiều lần về thời gian/chi phí; corpus/unit boundary có thể gây mất mạch ý. Cải tiến chỉ được chỉnh trên dev hoặc phải tạo test mới nếu dùng test hiện tại để thiết kế lại.", "",
        "## Tái lập và khai báo AI", "",
        "Xem PIPELINE.md và requirements-lab.txt. Lệnh: scripts/build_chunks.py → scripts/ingest_vectors.py → scripts/evaluate_dev.py → scripts/evaluate_test.py. Các evaluator từ chối ghi đè lựa chọn/test đã có để tránh vô tình dùng lại holdout; lệnh kiểm tra bài hiện có: scripts/validate_submission.py. Không commit .venv, secret hoặc .runtime/chroma.", "",
        "Dùng Codex AI hỗ trợ tìm nguồn, viết code, tạo câu hỏi, kiểm tra evidence, chạy thí nghiệm, đề xuất nhãn và soạn bản nháp này. Đã kiểm tra tự động token, offsets, lưu bền vững, nạp lại, hash split/config và trace. Học viên chưa hoàn tất kiểm tra nhãn thủ công; phải đọc hiểu code, gold và các nhận xét trước khi nhận bài là của mình.", "",
        "### Việc còn thiếu trước nộp", "",
        "- Đã xác nhận họ tên Nguyễn Thùy Dương, MSSV 2A202603388 và lớp L3A. Repo và tag phiên bản chốt đã ghi trong STUDENT.md.",
        "- Học viên chấm/ghi lý do và người chấm cho coherence, metadata, grounding; review evidence tương đương và gold. Không coi AI proposal là nhãn thủ công.",
        "- Tổng hợp lại chỉ số sau review riêng với số tự động; giữ dấu vết thay đổi và giải thích.",
        "- Repo được đặt công khai. Học viên nộp link phiên bản submission-day06 theo kênh và thời hạn của giảng viên.", "",
    ]
    if (ROOT / "results/audit/ai_summary.json").exists():
        ai = read("results/audit/ai_summary.json")
        lines += [
            "## Phụ lục: kết quả AI đã chấm riêng", "",
            "Codex AI đã chấm 30 mẫu coherence, 15 trường hợp grounding và đối chiếu 45 bản ghi metadata. Phần này là đánh giá AI, chưa phải nhãn thủ công đã được học viên xác nhận. Xem results/audit/AI_REVIEW.md, ai_summary.json và ai_assessments.jsonl để truy từng lý do, source và phương pháp. Các bảng đề xuất trước đó được lưu để thấy nguồn gốc nhận xét.", "",
            "| Cấu hình | Test Hit@1 sau AI review | Test Hit@3 sau AI review | Coherence AI /2 | Grounding AI /2 | Metadata AI đủ/đúng |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for name, item in ai["strategies"].items():
            ret = item["test_retrieval_after_AI_equivalent_evidence_review"]
            lines.append(f"| {name} | {ratio(ret['hit_at_1'])} | {ratio(ret['evidence_hit_at_3'])} | {item['coherence']['mean_out_of_2']:.2f} | {item['grounding']['mean_out_of_2']:.2f} | {item['metadata']['correct_and_complete']}/{item['metadata']['count']} |")
        lines += ["", "AI chấp nhận q16 như bằng chứng tương đương có đủ ngữ cảnh trong nguồn tổng quan, áp dụng nhất quán cả ba cấu hình. Không sửa benchmark, trace/chỉ số tự động hoặc lựa chọn C. Đây là số liệu sau AI review riêng, không phải dự báo và cũng không phải học viên đã chấm. Cùng AI tham gia tạo gold và đánh giá nên có nguy cơ thiên lệch; không có người chấm độc lập. Phần học viên đọc/chấm và thông tin cá nhân còn thiếu như checklist trên.", ""]
    content = "\n".join(lines)
    confirmation_path = ROOT / "results/audit/student_confirmation.json"
    if confirmation_path.exists():
        confirmation = read("results/audit/student_confirmation.json")
        human = read("results/audit/human_summary.json")
        reviewed = read("results/audit/confirmed_test/summary.json")
        assert human["all_human_audits_complete"]
        replacements = {
            "**Trạng thái:** pipeline và benchmark đã chạy; chưa hoàn thành nhãn thủ công của học viên. Các đề xuất AI được tách riêng. Chưa xác nhận đây là bài nộp hoàn chỉnh.": "**Trạng thái** Đã hoàn tất corpus, pipeline, benchmark và phiếu audit được Nguyễn Thùy Dương xác nhận. Bản báo cáo dùng số liệu thực đo và nêu các giới hạn của thí nghiệm.",
            "**Người chấm: Nguyễn Thùy Dương.** Trạng thái: chờ rà soát và xác nhận nhãn.": "**Người chấm: Nguyễn Thùy Dương.** Đã xác nhận phiếu nhãn và bằng chứng tương đương qua hội thoại; đây là xác nhận bản chấm có công cụ hỗ trợ, không phải chấm mù độc lập.",
            "nhãn học viên còn trống": "nhãn đã được Nguyễn Thùy Dương xác nhận",
            "chưa gọi là tỷ lệ đã audit thủ công": "các nhãn đối chiếu đã được Nguyễn Thùy Dương xác nhận, với nguồn gốc công cụ hỗ trợ được lưu riêng",
            "### Đề xuất AI — chưa phải kết quả chấm của học viên": "### Nhãn đã được học viên xác nhận",
            "Coherence AI đề xuất /2": "Coherence /2",
            "Grounding AI: số mức 0/1/2": "Grounding: số mức 0/1/2",
            "Grounding AI TB /2": "Grounding TB /2",
            "Chờ học viên đọc/chấm": "Nguyễn Thùy Dương xác nhận",
            "Học viên chưa hoàn tất kiểm tra nhãn thủ công; phải đọc hiểu code, gold và các nhận xét trước khi nhận bài là của mình.": "Nguyễn Thùy Dương đã xác nhận các nhãn và nhận xét qua hội thoại. Nguồn gốc hỗ trợ được lưu để minh bạch; không coi đánh giá này là chấm mù hoặc có người chấm độc lập.",
            "- Học viên chấm/ghi lý do và người chấm cho coherence, metadata, grounding; review evidence tương đương và gold. Không coi AI proposal là nhãn thủ công.": "- [x] Nguyễn Thùy Dương đã xác nhận 30 nhãn coherence, 15 grounding, 45 metadata và bằng chứng tương đương q16; xem results/audit/student_confirmation.json.",
            "- Tổng hợp lại chỉ số sau review riêng với số tự động; giữ dấu vết thay đổi và giải thích.": "- [x] Đã tổng hợp kết quả sau rà soát riêng với chỉ số tự động, giữ nguyên dấu vết và cấu hình đã chọn.",
            "Phần này là đánh giá AI, chưa phải nhãn thủ công đã được học viên xác nhận.": "Phần này lưu đánh giá gốc của công cụ; phiếu tương ứng đã được Nguyễn Thùy Dương xác nhận sau đó.",
            "Đây là số liệu sau AI review riêng, không phải dự báo và cũng không phải học viên đã chấm.": "Đây là số liệu công cụ soạn trước khi học viên xác nhận; kết quả xác nhận được trình bày riêng ở phần cuối.",
            "Phần học viên đọc/chấm và thông tin cá nhân còn thiếu như checklist trên.": "Phần xác nhận nhãn và thông tin học viên đã hoàn tất.",
            "cần ghi nhận sau review": "đã được học viên chấp nhận sau rà soát",
        }
        for old, new in replacements.items():
            content = content.replace(old, new)
        old_paragraph = "AI đề xuất chấp nhận q16 top-1 của cả ba cấu hình: “Bản in đen chờ cho khô thì đem tô màu.” trong hoi_hoa_dan_gian_u008, văn cảnh xác định tranh làng Sình. Nếu được học viên xác nhận và không có sửa đổi review khác, test sẽ là A Hit@1 2/5 và Hit@3 2/5; B 1/5 và 2/5; C 1/5 và 3/5. Chưa dùng các số dự kiến này thay số tự động hoặc chọn lại cấu hình."
        content = content.replace(old_paragraph, "Nguyễn Thùy Dương đã xác nhận bằng chứng tương đương q16 ở top-1 của cả ba cấu hình: “Bản in đen chờ cho khô thì đem tô màu.” trong hoi_hoa_dan_gian_u008, có văn cảnh làng Sình. Số liệu sau review được tổng hợp riêng ở cuối báo cáo, không sửa số tự động hoặc lựa chọn C.")
        content += "\n## Kết quả sau xác nhận của người chấm\n\nNgười chấm: **Nguyễn Thùy Dương**. Phương thức: xác nhận phiếu đánh giá được trợ lý hỗ trợ soạn, qua phát biểu “ok tôi xác nhận rồi”. Không khai là đánh giá độc lập. Hồ sơ: results/audit/student_confirmation.json; nhãn chi tiết ở các packet coherence/grounding/metadata.jsonl.\n\n| Cấu hình | Hit@1 test sau review | Hit@3 test sau review | Coherence /2 | Grounding /2 | Metadata đủ/đúng | Filter test tuân thủ |\n|---|---:|---:|---:|---:|---:|---:|\n"
        for name in ["A", "B", "C"]:
            ret, audit = reviewed["strategies"][name], human["strategies"][name]
            content += f"| {name} | {ratio(ret['hit_at_1'])} | {ratio(ret['evidence_hit_at_3'])} | {audit['coherence']['mean_of_reviewed']:.2f} (10 mẫu) | {audit['grounding']['mean_of_reviewed']:.2f} (5 câu) | {audit['metadata']['complete_and_correct']}/15 | {ratio(ret['filter_compliance'])} |\n"
        content += "\nChỉ bổ sung việc chấp nhận nguồn evidence tương đương q16. Các cấu hình, câu hỏi, vector và lựa chọn từ dev không thay đổi; nguồn số liệu tự động vẫn nằm trong results/test, số sau review ở results/audit/confirmed_test.\n"
    path = ROOT / "report/individual/2A202603388_NguyenThuyDuong.md"
    path.write_text(content, encoding="utf-8")
    print("Report and experiment log updated. Student confirmation:", confirmation_path.exists())


if __name__ == "__main__":
    main()
