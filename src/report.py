"""Render report from measured artifacts; never supplies missing human scores."""
from .common import ROOT,read_json,read_jsonl,now


def render():
    manifest=read_json(ROOT/'data/manifest.json')
    stats=read_json(ROOT/'results/ingestion_stats.json')
    metrics=read_json(ROOT/'results/metrics.json')
    audit=read_json(ROOT/'results/audit_summary.json')
    runtime=read_json(ROOT/'results/runtime.json')
    selection=read_json(ROOT/'results/selection.json')
    frozen=read_json(ROOT/'benchmark/frozen.json')
    model=runtime['model']
    lines=[
'# Báo cáo cá nhân — Day 6: Tra cứu Kanji N2', '',
'**Học viên:** Nguyễn Thị Thanh Bình · **MSSV:** 2A202603497 · **Lớp:** L3A',
'**Ngày chạy:** 13/11/2026 (Asia/Ho_Chi_Minh). **Công cụ hỗ trợ:** Codex.', '',
'## 1. Mục tiêu và dữ liệu','',
'Xây kho tri thức tra cứu chữ Kanji, âm Hán Việt, Onyomi/Kunyomi, mẹo nhớ và từ phái sinh từ tài liệu Kanji N2; so sánh tác động của chunking và metadata filter. Công cụ trả về đoạn nguồn và trang, không sinh câu trả lời bằng LLM.', '',
f'Corpus: **{manifest["physical_pages"]} trang vật lý**, **{manifest["included_content_pages"]} trang nội dung**, **{manifest["kanji_entries"]} mục Kanji**, **{manifest["vocabulary_entries"]} mục từ phái sinh**, 16 bài. Tổng **{manifest["normalized_char_count"]:,} ký tự** trên trang nội dung sau NFC và gộp khoảng trắng. Không trừ riêng từng ô luyện viết nhưng các ô trống không tạo thêm text hoặc trang. Các trang học có nội dung chữ đủ dùng; không nhân bản để đủ số lượng.', '',
'Giữ toàn bộ 454 trang học; bỏ 19 trang: bìa, mục lục, 16 trang tổng quan bài và trang hướng dẫn/nguồn cuối. Trang PDF đánh số từ 1, giữ được đường dẫn về bản gốc. Manifest chứa danh sách từng trang, số ký tự, quy tắc tính, nguồn, quyền và hash.', '',
'**Nguồn/quyền:** Sensei của học viên biên soạn, tác giả hiển thị Kaori Sensei. Học viên xác nhận ngày 13/11/2026 đã được sensei cho phép sử dụng, đổi lại gửi công cụ dùng thử. Chưa suy ra quyền phát hành công khai toàn bộ PDF. PDF, corpus trích xuất, model, Qdrant và trace đầy đủ lưu local/được Git ignore. Người chấm nhận nguồn riêng từ học viên để tái lập. Trang cuối ghi JMdict/EDRDG, CC BY-SA 4.0 cho dữ liệu từ vựng; giữ ghi công, không gán giấy phép đó cho mọi ảnh/nội dung trong PDF.', '',
f'**SHA-256 PDF:** `{manifest["sha256"]}`.', '',
'## 2. Pipeline, model và metadata','',
'Python + pypdf đọc từng trang → NFC, bỏ dòng rỗng → parse mục Kanji theo nhãn và bảng từ → chuẩn hóa các trường bằng nhãn và dấu `|` → chia chunk → embedding local → Qdrant persistent → cosine top-3. ID chunk gồm nguồn, cấu hình, trang, vị trí và hash nội dung. Không lập chỉ mục hình minh họa/ô luyện viết.', '',
f'Đọc PDF mất **{manifest["extraction_seconds"]:.3f}s**. Có **{manifest["error_count"]} lỗi trang/parser**; không có trang rỗng. pypdf có cảnh báo font CMap hex độ dài lẻ lặp lại, lưu nguyên tại `results/extraction_warnings.log`. Không coi “không lỗi parser” là bằng chứng mọi ký tự hiếm đều đúng. Đã xem trang mẫu 4 bằng render và đối chiếu chữ/bảng; gold 20 câu kiểm tra lại với text nguồn. Cần sensei kiểm tra ký tự hiếm, cách đọc và mẹo nhớ trước dùng chính thức.', '',
f'**Embedding:** `{model["model"]}`, revision `{model["revision"]}`, 384 chiều, MIT; Sentence Transformers chạy CPU, chuẩn hóa vector L2. Document prefix `passage: `, query prefix `query: ` cho cả tiếng Việt/Nhật. Giới hạn 512 token; chunk dài nhất {max(s["max_tokens"] for s in stats.values())} token, không chunk nào bị cắt ở tokenizer. Seed 0; CPU 4 luồng. Không dùng mock/TF-IDF thay embedding.', '',
f'**Vector store:** Qdrant local persistent, qdrant-client {runtime["packages"]["qdrant-client"]}, `.local/qdrant`, 3 collection `kanji_A/B/C`, cosine, exact search. Kiểm tra count sau ingest, lặp upsert và đóng/mở lại database đều bằng số chunk, không nhân đôi. Khi tài liệu đổi: ingest lại rồi build; build thay toàn bộ collection lab tương ứng để xóa chunk cũ, không phải cập nhật delta. Benchmark khóa hash sẽ yêu cầu một thí nghiệm mới nếu corpus/cấu hình đổi.', '',
'**Metadata:** `document_id` (string ID nguồn), `source` (string tên PDF), `page` (integer số trang vật lý), `lesson` (integer lấy từ tiêu đề Bài NN), `kanji`, `han_viet` (string lấy từ nội dung). `lesson` hữu ích để giới hạn bài ôn; đủ 16 giá trị được kiểm chứng từ nguồn. Không tự thêm năm, cấp JLPT cho từng từ hoặc giá trị không có trong tài liệu.', '',
'## 3. Cấu hình và benchmark','',
'| Cấu hình | Chunking | Filter |', '|---|---|---|',
'| A | Cửa sổ 220 ký tự, overlap 40, không vượt ranh giới mục Kanji | Không |',
'| B | Giữ nguyên một mục Kanji cùng âm đọc/cách nhớ/tất cả từ phái sinh | Không |',
'| C | Text và vector giống B | Lọc lesson chỉ khi câu hỏi cung cấp số bài |','',
'A–B chỉ thay cách chia chunk; metadata được gắn giống nhau. B–C chỉ thay filter. C dùng lại vector B để kiểm soát so sánh và tiết kiệm chi phí; thời gian C không được diễn giải thành model nhanh hơn.', '',
f'20 câu đã khóa lúc **{frozen["frozen_at"]}**, trước truy xuất: 15 dev (bài 01–12), 5 test (bài 13–16). Có 7 câu filter (5 dev, 2 test), gồm câu diễn đạt lại và phân biệt nghĩa. Mỗi câu có đáp án, nguồn/trang, raw quote và canonical evidence; evidence kiểm tra tồn tại trong trang trước chạy. Ghi mọi trang có evidence giống nhau; nguồn tương đương diễn đạt khác cần người chấm xác nhận thêm. Không dùng gold làm input truy xuất.', '',
'Hit@1 = số câu top1 đúng nguồn/trang và chứa đủ evidence / số câu. Evidence Hit@3 = số câu có ít nhất một chunk trong top3 thỏa cùng điều kiện / số câu. Không ghép evidence từ nhiều chunk. Canonical labels/`|` là chuẩn hóa cấu trúc, không thay nghĩa. Không dùng kết quả này để khẳng định độ chính xác câu trả lời LLM.', '',
f'Quy tắc chọn trước test: dev Hit@3 → Hit@1 → ít chunk → B/C/A. Đã chọn **{selection["selected"]}** lúc **{selection["frozen_at"]}**, trước khi truy xuất test. Không đổi tham số sau xem test; kết quả test chỉ minh họa cuối cùng.', '',
'## 4. Kết quả truy xuất và tài nguyên','',
'| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunks | Ingest (s) | API cost |',
'|---|---|---|---|---:|---:|---:|']
    for m in metrics:
        s=stats[m['strategy']]
        lines.append(f'| {m["strategy"]} | {m["split"]} | {m["hit1_n"]}/{m["n"]} ({m["hit1"]:.1%}) | {m["hit3_n"]}/{m["n"]} ({m["hit3"]:.1%}) | {s["chunk_count"]} | {s["ingest_seconds"]:.3f} | $0 |')
    lines += ['', 'Ingest gồm tokenize, embedding, ghi vector và lặp upsert kiểm tra. Không gồm tải model, khởi động model hoặc đọc PDF. C dùng lại embedding B; nếu chạy riêng cần embedding như B. API cost $0; chưa đo điện, phần cứng và lưu trữ. Số liệu thời gian là một lần chạy trên máy này, không benchmark hiệu năng nhiều lần.', '',
'| Strategy | Ký tự min / mean / max | Tổng ký tự chunk | Tổng token | Embedding (s) | Dev search mean (ms) | Test search mean (ms) |',
'|---|---|---:|---:|---:|---:|---:|']
    for name,s in stats.items():
        d=next(m for m in metrics if m['strategy']==name and m['split']=='dev')
        t=next(m for m in metrics if m['strategy']==name and m['split']=='test')
        lines.append(f'| {name} | {s["char_min"]} / {s["char_mean"]:.1f} / {s["char_max"]} | {s["total_chars"]} | {s["total_tokens"]} | {s["embedding_seconds"]:.3f} | {d["mean_search_ms"]:.3f} | {t["mean_search_ms"]:.3f} |')
    lines += ['', 'Search time chỉ đo Qdrant, không gồm embedding query; filter local có thể chậm hơn trên corpus nhỏ. A có overlap nên tổng ký tự/token lớn hơn dù từng chunk ngắn hơn.', '',
'## 5. Coherence, metadata và grounding','',
'**Tính trung thực về nhãn:** Bảng dưới dùng nhãn do **Codex AI hỗ trợ đọc trực tiếp** các mẫu (không thấy similarity score trong packet coherence/grounding), kèm lý do từng trường hợp. Đây **chưa phải chấm thủ công độc lập của học viên**, chưa được dùng để tuyên bố hoàn tất yêu cầu human audit. Tác giả cần đọc packet và điền/xác nhận các CSV student review trước nộp. Không tự ghi học viên là người đã chấm.', '',
'| Strategy | AI coherence /2 (n) | Metadata đúng/đủ đối chiếu nguồn | Top3 tuân thủ bài yêu cầu (câu test) | AI grounding 0/1/2; mean /2 |',
'|---|---|---|---|---|']
    for name,a in audit.items():
        counts=a['grounding_score_counts']
        lines.append(f'| {name} | {a["ai_coherence_mean"]:.2f} (10) | {a["metadata_correct_n"]}/{a["metadata_total"]} | {a["filter_compliance_questions_n"]}/{a["filter_questions_total"]} | {counts["0"]}/{counts["1"]}/{counts["2"]}; {a["ai_grounding_mean"]:.2f} |')
    lines += ['',
'Coherence: chọn trước 10 trang nội dung đầu (4–13), mốc từ cuối bảng từ; A lấy chunk xuất hiện sớm nhất chứa từ mốc, B/C cùng vị trí nguồn. Thang 0: đứt ý không hiểu; 1: hiểu một phần/thiếu ngữ cảnh; 2: tự hiểu và trọn ý. A có 7 mẫu mức 1 và 3 mẫu mức 2. B/C giữ cả mục, 10 mẫu mức 2. Mẫu chỉ ở bài 01 nên có thiên lệch vị trí; không khái quát toàn bộ corpus.', '',
'Metadata: kiểm tra 5 test × top3 = 15 bản ghi mỗi chiến lược. Code đối chiếu số trang, tiêu đề bài và chữ Kanji với raw source; AI đọc packet để rà sự nhất quán; kết quả đối chiếu tự động là 45/45. Không coi đủ trường là chứng minh retrieval đúng. Q16/Q19 có filter: A tự tình cờ tuân thủ 1/2 câu, B 0/2, C 2/2. A/B không bật filter nên đây là đo khả năng giữ phạm vi, không gọi là lỗi backend. Với 3 câu test không yêu cầu filter: N/A, không mặc định 100%.', '',
'Grounding: đọc top3 cho Q16–Q20 ở từng cấu hình, 0 không có evidence, 1 có nhưng thiếu phần cần thiết, 2 đủ trả lời và truy nguồn. Tất cả 15 trường hợp AI chấm 2 vì đúng từ/cách đọc/nghĩa trong một đoạn; ví dụ A-Q17 top1 bắt đầu bằng mảnh từ trước nhưng vẫn chứa đủ 半壊/はんかい/một phần. Coherence thấp ở một đoạn không đồng nghĩa câu hỏi cụ thể thiếu evidence. Không tính grounding bằng công thức Hit@3.', '',
'## 6. Phân tích tác động và lỗi','',
'**A–B:** dev Hit@3 tăng 13/15 → 15/15; số chunk giảm 774 → 454. B giữ quan hệ chữ–âm–nghĩa, giảm mất evidence tại ranh giới và giảm tổng token. Trên test, cả hai 5/5 nên test này không phân biệt được ưu thế.', '',
'**B–C:** Hit@1/3 dev và test không tăng. Lọc bài làm top3 đúng phạm vi ở cả 2 câu test filter, hữu ích khi sensei giao ôn riêng một bài. Ví dụ Q19: B trả trang 439 (bài16), 427 (bài15), 440 (bài16); C bỏ trang 427, chỉ giữ bài16. Filter không bảo đảm xếp hạng đầu đúng nghĩa, cũng loại đáp án hợp lệ nếu người dùng nhập sai bài.', '',
'Các lỗi có thể kiểm chứng trong trace:', '',
'- **A-Q10**, trang 172: top1 đúng mục 契 nhưng cắt ở “契約書 | けいやくしょ | văn bả”, thiếu nghĩa hoàn chỉnh “văn bản hợp đồng”. Top3 không có chunk đủ evidence nên Hit@3=0. B/C giữ trọn mục, sửa lỗi này.',
'- **A-Q13**, trang 259: đoạn đúng cắt “持参 | じさん | mang”, thiếu “theo”. B/C đưa đoạn đủ lên top2; vẫn xếp 伺 (trang272) ở top1 nên Hit@1 còn sai.',
'- **B/C-Q09**, trang144: câu hỏi 改札 nhưng top1 là 改札口 ở trang154. Hai từ gần nhau về nghĩa/hình thức; cosine dense chưa phân biệt chính xác bề mặt từ. Đáp án đúng 改札 ở top2. Có thể thử exact-word/hybrid trong thí nghiệm mới, chưa triển khai hoặc đo ở đây.', '',
'**Chọn B** làm baseline theo quy tắc dev đã chốt: bằng C về retrieval, ít chunk hơn A, không yêu cầu filter đầu vào. Bản dùng thử cho sensei cho phép chế độ C khi người dùng chủ động chọn bài; đây là tùy chọn phạm vi, không sửa quyết định benchmark.', '',
'## 7. Tái lập, giới hạn và phần học viên cần xác nhận','',
'Chạy theo README: tạo venv, cài requirements.lock.txt (bản macOS/CPU đã chạy), nhận PDF đúng hash, download model đúng revision, ingest, build, benchmark, xuất packet audit. Môi trường khác có thể cài requirements.txt rồi ghi phiên bản mới. `python -m unittest discover -s tests -v` kiểm tra corpus/gold, ranh giới evidence, bảo toàn chunk và Qdrant reload/filter. Demo: `python -m src.run interactive` hoặc `TraCuuKanji.command`.', '',
'Kết quả chính: `results/metrics.csv`, `ingestion_stats.json`, `runtime.json`, `selection.json`; trace đầy đủ `results/private/traces.jsonl` (60 lượt truy xuất, 180 chunk), summary bỏ text `results/retrieval_summary.jsonl`. Nhãn AI và lý do: `ai_coherence_review.jsonl`, `ai_grounding_review.jsonl`. Metadata: `metadata_audit.jsonl`. Packet đọc: `results/private/REVIEW_PACKET.md`. Nhật ký giả thuyết: `artifacts/experiment_log.csv`.', '',
'**Cần học viên làm trước khi nộp:** đọc packet, chấm/xác nhận 30 coherence, 15 grounding và 45 metadata record; điền `student_coherence_review.csv`, `student_grounding_review.csv`, `student_metadata_review.csv`, rồi chạy `python -m src.finalize_review`. Học viên chịu trách nhiệm giải thích code/kết quả. Link repo đã được học viên nộp trên LMS; bản cập nhật được chốt bằng tag day06-submission-2026-11-13.', '',
'Giới hạn: test chỉ 5 câu, cùng một tài liệu/template nên có rò rỉ từ vựng và thiên lệch câu tra từ; gold/AI audit cùng một trợ lý nên không độc lập. Chưa kiểm chứng toàn bộ kiến thức tiếng Nhật, chưa tìm theo ảnh/nét viết, chưa đánh giá câu không có đáp án, lỗi gõ, mọi cách hỏi khác hoặc nguồn tương đương khác diễn đạt. Mẫu 100% test không chứng minh hệ thống đúng mọi câu; cosine luôn trả nearest chunks dù không liên quan. Chưa thu góp ý thực tế từ sensei. Nếu mở rộng: benchmark lớn hơn, người chấm độc lập, thêm exact-word/hybrid có đối chứng dev/test mới, kiểm tra glyph và các ô âm đọc thiếu.', '',
'Không phát sinh chi phí API trả phí. Tải thư viện/model dùng mạng; nội dung PDF không gửi embedding API. Các log lỗi setup/runtime được lưu; không fallback sang mock.', '']
    student=ROOT/'results/student_audit_summary.json'
    if student.exists():
        lines += ['## 8. Nhãn học viên đã xác nhận','',
                  'Kết quả học viên từ `results/student_audit_summary.json` (giữ riêng nhãn AI để đối chiếu):','',
                  '```json',student.read_text(encoding='utf-8').strip(),'```','']
    path=ROOT/'report/individual/2A202603497_NguyenThiThanhBinh.md'
    from .report_ui import update_report
    path.write_text(update_report('\n'.join(lines)),encoding='utf-8')
    print(path)

if __name__=='__main__':render()
