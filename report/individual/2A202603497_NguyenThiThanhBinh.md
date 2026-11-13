# Báo cáo cá nhân — Day 6: Tra cứu Kanji N2

**Học viên:** Nguyễn Thị Thanh Bình · **MSSV:** 2A202603497 · **Lớp:** L3A
**Ngày chạy:** 13/11/2026 (Asia/Ho_Chi_Minh). **Công cụ hỗ trợ:** Codex.

## 1. Mục tiêu và dữ liệu

Xây kho tri thức tra cứu chữ Kanji, âm Hán Việt, Onyomi/Kunyomi, mẹo nhớ và từ phái sinh từ tài liệu Kanji N2; so sánh tác động của chunking và metadata filter. Công cụ trả về đoạn nguồn và trang, không sinh câu trả lời bằng LLM.

Corpus: **473 trang vật lý**, **454 trang nội dung**, **454 mục Kanji**, **1764 mục từ phái sinh**, 16 bài. Tổng **150,746 ký tự** trên trang nội dung sau NFC và gộp khoảng trắng. Không trừ riêng từng ô luyện viết nhưng các ô trống không tạo thêm text hoặc trang. Các trang học có nội dung chữ đủ dùng; không nhân bản để đủ số lượng.

Giữ toàn bộ 454 trang học; bỏ 19 trang: bìa, mục lục, 16 trang tổng quan bài và trang hướng dẫn/nguồn cuối. Trang PDF đánh số từ 1, giữ được đường dẫn về bản gốc. Manifest chứa danh sách từng trang, số ký tự, quy tắc tính, nguồn, quyền và hash.

**Nguồn/quyền:** Kaori Sensei biên soạn. Học viên xác nhận ngày 13/11/2026 đã được sensei cho phép sử dụng, đổi lại gửi công cụ dùng thử. PDF, corpus trích xuất, model, Qdrant và trace đầy đủ lưu local/được Git ignore. Người chấm nhận nguồn riêng từ học viên để tái lập. Trang cuối ghi JMdict/EDRDG, CC BY-SA 4.0 cho dữ liệu từ vựng; giữ ghi công, không gán giấy phép đó cho mọi ảnh/nội dung trong PDF.

**SHA-256 PDF:** `0d720e9a79d6b86ca74326083d7c1bb87dc2a245c5f7c4e0e44e4a7f15bd5fa5`.

## 2. Pipeline, model và metadata

Python + pypdf đọc từng trang → NFC, bỏ dòng rỗng → parse mục Kanji theo nhãn và bảng từ → chuẩn hóa các trường bằng nhãn và dấu `|` → chia chunk → embedding local → Qdrant persistent → cosine top-3. ID chunk gồm nguồn, cấu hình, trang, vị trí và hash nội dung. Không lập chỉ mục hình minh họa/ô luyện viết.

Đọc PDF mất **8.109s**. Có **0 lỗi trang/parser**; không có trang rỗng. pypdf có cảnh báo font CMap hex độ dài lẻ lặp lại, lưu nguyên tại `results/extraction_warnings.log`. Không coi “không lỗi parser” là bằng chứng mọi ký tự hiếm đều đúng. Đã xem trang mẫu 4 bằng render và đối chiếu chữ/bảng; gold 20 câu kiểm tra lại với text nguồn. Cần sensei kiểm tra ký tự hiếm, cách đọc và mẹo nhớ trước dùng chính thức.

**Embedding:** `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, 384 chiều, MIT; Sentence Transformers chạy CPU, chuẩn hóa vector L2. Document prefix `passage: `, query prefix `query: ` cho cả tiếng Việt/Nhật. Giới hạn 512 token; chunk dài nhất 156 token, không chunk nào bị cắt ở tokenizer. Seed 0; CPU 4 luồng. Không dùng mock/TF-IDF thay embedding.

**Vector store:** Qdrant local persistent, qdrant-client 1.20.0, `.local/qdrant`, 3 collection `kanji_A/B/C`, cosine, exact search. Kiểm tra count sau ingest, lặp upsert và đóng/mở lại database đều bằng số chunk, không nhân đôi. Khi tài liệu đổi: ingest lại rồi build; build thay toàn bộ collection lab tương ứng để xóa chunk cũ, không phải cập nhật delta. Benchmark khóa hash sẽ yêu cầu một thí nghiệm mới nếu corpus/cấu hình đổi.

**Metadata:** `document_id` (string ID nguồn), `source` (string tên PDF), `page` (integer số trang vật lý), `lesson` (integer lấy từ tiêu đề Bài NN), `kanji`, `han_viet` (string lấy từ nội dung). `lesson` hữu ích để giới hạn bài ôn; đủ 16 giá trị được kiểm chứng từ nguồn. Không tự thêm năm, cấp JLPT cho từng từ hoặc giá trị không có trong tài liệu.

## 3. Cấu hình và benchmark

| Cấu hình | Chunking | Filter |
|---|---|---|
| A | Cửa sổ 220 ký tự, overlap 40, không vượt ranh giới mục Kanji | Không |
| B | Giữ nguyên một mục Kanji cùng âm đọc/cách nhớ/tất cả từ phái sinh | Không |
| C | Text và vector giống B | Lọc lesson chỉ khi câu hỏi cung cấp số bài |

A–B chỉ thay cách chia chunk; metadata được gắn giống nhau. B–C chỉ thay filter. C dùng lại vector B để kiểm soát so sánh và tiết kiệm chi phí; thời gian C không được diễn giải thành model nhanh hơn.

20 câu đã khóa lúc **2026-11-13T17:07:22.700049+07:00**, trước truy xuất: 15 dev (bài 01–12), 5 test (bài 13–16). Có 7 câu filter (5 dev, 2 test), gồm câu diễn đạt lại và phân biệt nghĩa. Mỗi câu có đáp án, nguồn/trang, raw quote và canonical evidence; evidence kiểm tra tồn tại trong trang trước chạy. Ghi mọi trang có evidence giống nhau; nguồn tương đương diễn đạt khác cần người chấm xác nhận thêm. Không dùng gold làm input truy xuất.

Hit@1 = số câu top1 đúng nguồn/trang và chứa đủ evidence / số câu. Evidence Hit@3 = số câu có ít nhất một chunk trong top3 thỏa cùng điều kiện / số câu. Không ghép evidence từ nhiều chunk. Canonical labels/`|` là chuẩn hóa cấu trúc, không thay nghĩa. Không dùng kết quả này để khẳng định độ chính xác câu trả lời LLM.

Quy tắc chọn trước test: dev Hit@3 → Hit@1 → ít chunk → B/C/A. Đã chọn **B** lúc **2026-11-13T17:12:06.104264+07:00**, trước khi truy xuất test. Không đổi tham số sau xem test; kết quả test chỉ minh họa cuối cùng.

## 4. Kết quả truy xuất và tài nguyên

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunks | Ingest (s) | API cost |
|---|---|---|---|---:|---:|---:|
| A | dev | 12/15 (80.0%) | 13/15 (86.7%) | 774 | 11.122 | $0 |
| A | test | 5/5 (100.0%) | 5/5 (100.0%) | 774 | 11.122 | $0 |
| B | dev | 13/15 (86.7%) | 15/15 (100.0%) | 454 | 9.052 | $0 |
| B | test | 5/5 (100.0%) | 5/5 (100.0%) | 454 | 9.052 | $0 |
| C | dev | 13/15 (86.7%) | 15/15 (100.0%) | 454 | 0.547 | $0 |
| C | test | 5/5 (100.0%) | 5/5 (100.0%) | 454 | 0.547 | $0 |

Ingest gồm tokenize, embedding, ghi vector và lặp upsert kiểm tra. Không gồm tải model, khởi động model hoặc đọc PDF. C dùng lại embedding B; nếu chạy riêng cần embedding như B. API cost $0; chưa đo điện, phần cứng và lưu trữ. Số liệu thời gian là một lần chạy trên máy này, không benchmark hiệu năng nhiều lần.

| Strategy | Ký tự min / mean / max | Tổng ký tự chunk | Tổng token | Embedding (s) | Dev search mean (ms) | Test search mean (ms) |
|---|---|---:|---:|---:|---:|---:|
| A | 41 / 153.2 / 220 | 118548 | 63191 | 9.897 | 1.094 | 0.700 |
| B | 167 / 232.9 / 298 | 105748 | 54739 | 8.400 | 0.406 | 0.408 |
| C | 167 / 232.9 / 298 | 105748 | 54739 | 0.000 | 1.153 | 1.386 |

Search time chỉ đo Qdrant, không gồm embedding query; filter local có thể chậm hơn trên corpus nhỏ. A có overlap nên tổng ký tự/token lớn hơn dù từng chunk ngắn hơn.

## 5. Coherence, metadata và grounding

**Tính trung thực về nhãn:** Bảng dưới dùng nhãn do **Codex AI hỗ trợ đọc trực tiếp** các mẫu (không thấy similarity score trong packet coherence/grounding), kèm lý do từng trường hợp. Đây **chưa phải chấm thủ công độc lập của học viên**, chưa được dùng để tuyên bố hoàn tất yêu cầu human audit. Tác giả cần đọc packet và điền/xác nhận các CSV student review trước nộp. Không tự ghi học viên là người đã chấm.

| Strategy | AI coherence /2 (n) | Metadata đúng/đủ đối chiếu nguồn | Top3 tuân thủ bài yêu cầu (câu test) | AI grounding 0/1/2; mean /2 |
|---|---|---|---|---|
| A | 1.30 (10) | 15/15 | 1/2 | 0/0/5; 2.00 |
| B | 2.00 (10) | 15/15 | 0/2 | 0/0/5; 2.00 |
| C | 2.00 (10) | 15/15 | 2/2 | 0/0/5; 2.00 |

Coherence: chọn trước 10 trang nội dung đầu (4–13), mốc từ cuối bảng từ; A lấy chunk xuất hiện sớm nhất chứa từ mốc, B/C cùng vị trí nguồn. Thang 0: đứt ý không hiểu; 1: hiểu một phần/thiếu ngữ cảnh; 2: tự hiểu và trọn ý. A có 7 mẫu mức 1 và 3 mẫu mức 2. B/C giữ cả mục, 10 mẫu mức 2. Mẫu chỉ ở bài 01 nên có thiên lệch vị trí; không khái quát toàn bộ corpus.

Metadata: kiểm tra 5 test × top3 = 15 bản ghi mỗi chiến lược. Code đối chiếu số trang, tiêu đề bài và chữ Kanji với raw source; AI đọc packet để rà sự nhất quán; kết quả đối chiếu tự động là 45/45. Không coi đủ trường là chứng minh retrieval đúng. Q16/Q19 có filter: A tự tình cờ tuân thủ 1/2 câu, B 0/2, C 2/2. A/B không bật filter nên đây là đo khả năng giữ phạm vi, không gọi là lỗi backend. Với 3 câu test không yêu cầu filter: N/A, không mặc định 100%.

Grounding: đọc top3 cho Q16–Q20 ở từng cấu hình, 0 không có evidence, 1 có nhưng thiếu phần cần thiết, 2 đủ trả lời và truy nguồn. Tất cả 15 trường hợp AI chấm 2 vì đúng từ/cách đọc/nghĩa trong một đoạn; ví dụ A-Q17 top1 bắt đầu bằng mảnh từ trước nhưng vẫn chứa đủ 半壊/はんかい/một phần. Coherence thấp ở một đoạn không đồng nghĩa câu hỏi cụ thể thiếu evidence. Không tính grounding bằng công thức Hit@3.

## 6. Phân tích tác động và lỗi

**A–B:** dev Hit@3 tăng 13/15 → 15/15; số chunk giảm 774 → 454. B giữ quan hệ chữ–âm–nghĩa, giảm mất evidence tại ranh giới và giảm tổng token. Trên test, cả hai 5/5 nên test này không phân biệt được ưu thế.

**B–C:** Hit@1/3 dev và test không tăng. Lọc bài làm top3 đúng phạm vi ở cả 2 câu test filter, hữu ích khi sensei giao ôn riêng một bài. Ví dụ Q19: B trả trang 439 (bài16), 427 (bài15), 440 (bài16); C bỏ trang 427, chỉ giữ bài16. Filter không bảo đảm xếp hạng đầu đúng nghĩa, cũng loại đáp án hợp lệ nếu người dùng nhập sai bài.

Các lỗi có thể kiểm chứng trong trace:

- **A-Q10**, trang 172: top1 đúng mục 契 nhưng cắt ở “契約書 | けいやくしょ | văn bả”, thiếu nghĩa hoàn chỉnh “văn bản hợp đồng”. Top3 không có chunk đủ evidence nên Hit@3=0. B/C giữ trọn mục, sửa lỗi này.
- **A-Q13**, trang 259: đoạn đúng cắt “持参 | じさん | mang”, thiếu “theo”. B/C đưa đoạn đủ lên top2; vẫn xếp 伺 (trang272) ở top1 nên Hit@1 còn sai.
- **B/C-Q09**, trang144: câu hỏi 改札 nhưng top1 là 改札口 ở trang154. Hai từ gần nhau về nghĩa/hình thức; cosine dense chưa phân biệt chính xác bề mặt từ. Đáp án đúng 改札 ở top2. UI đã bổ sung ưu tiên từ khớp để xử lý trải nghiệm này; chưa đo tác động đó bằng benchmark mới. Hybrid vẫn là hướng mở rộng.

**Chọn B** làm baseline theo quy tắc dev đã chốt: bằng C về retrieval, ít chunk hơn A, không yêu cầu filter đầu vào. Bản dùng thử cho sensei cho phép chế độ C khi người dùng chủ động chọn bài; đây là tùy chọn phạm vi, không sửa quyết định benchmark.

## 7. Công cụ tra cứu dùng thử cho sensei

### 7.1. Mục đích và giao diện

Phần mở rộng chuyển kho dữ liệu thành công cụ tra cứu local để học viên và sensei dùng thử. UI có **một ô tìm kiếm chung**, tự nhận biết nội dung nhập; không có nút yêu cầu người dùng chọn loại tìm kiếm. Người dùng có thể lọc theo 16 bài học. Kết quả gồm Kanji, âm Hán Việt, Onyomi/Kunyomi, cách nhớ, từ phái sinh và liên kết tới đúng trang PDF nguồn.

Phần viết tay có **một ô chữ mễ**, hỗ trợ sự kiện chuột/bút/cảm ứng; có hoàn tác nét, xóa và chọn một trong **8 ứng viên** gần hình dạng. Tám ứng viên là danh sách gợi ý cho một chữ, không phải tám ô viết. Đã kiểm tra thao tác chuột trên trình duyệt; chưa kiểm tra bằng thiết bị cảm ứng thực.

Mã nguồn: `src/web.py`, `src/lookup.py`, `src/handwriting.py`, `ui/index.html`, `ui/app.js`, `ui/style.css`. Server Python chỉ nghe `127.0.0.1:8766`. Sau khi chuẩn bị model và dữ liệu, tra cứu/nhận dạng chạy local; không gửi PDF hoặc nét viết tới API. Nét viết chỉ giữ trong bộ nhớ phiên trang, không ghi vào log hoặc database.

### 7.2. Hành vi tìm kiếm đã hiện thực

| Nội dung nhập | Xử lý | Ví dụ đã kiểm tra |
|---|---|---|
| Kanji hoặc cách đọc tiếng Nhật | Đối chiếu chữ/từ/cách đọc trong nguồn; không tự ghép kết quả vector không liên quan vào kết quả chính | `天井` trả mục chứa `天井` và cách đọc `てんじょう` |
| Chữ/từ chưa khớp | Hiện “Có phải bạn muốn tìm?” bằng các từ gần cách viết; với một chữ có thể so hình dạng glyph bằng font Nhật local | `資額` có gợi ý `金額`, `資金`, `資料`…; người dùng quyết định chữ muốn tìm |
| Âm Hán Việt | Không phân biệt hoa/thường hoặc dấu khi tìm nhóm; ưu tiên đúng dấu đã nhập, các âm gần dạng không dấu nằm dưới tiêu đề riêng | `Tinh` tìm nhóm TINH/TÍNH/TÌNH/TỊNH/TỈNH có trong tài liệu; `TỈNH` đưa `井`, `省` lên đầu |
| Ngữ nghĩa tiếng Việt | Đối chiếu nghĩa trong nguồn ở dạng không dấu trước; nếu chưa khớp thì dùng embedding và Qdrant | `cây thông` / `cay thong` → `松 — TÙNG`, trang 363; `miễn thuế` / `mien thue` → `免 — MIỄN` |
| Miêu tả / cách gợi nhớ | Nhận biết các từ chỉ hình dạng/cấu tạo/cách nhớ; đối chiếu mẹo nhớ không dấu, sau đó dùng collection mnemonic khi cần tìm gần nghĩa | `cai gieng 2 tang`, `giong cai gieng` → `井 — TỈNH`, trang 4 |

Đối chiếu không dấu dùng Unicode NFD, bỏ dấu kết hợp, chuyển `đ` thành `d`, gộp khoảng trắng và không phân biệt hoa/thường. Nội dung hiển thị giữ nguyên tiếng Việt có dấu. Các mô tả có thêm từ như “tìm”, “giống”, “chữ” được kiểm tra bằng từ nội dung sau bỏ một số từ chức năng; cách này là heuristic, không phải phân tích ngôn ngữ hoàn chỉnh.

Kết quả khớp chính xác và phần **“Lưu ý: từ tương tự”** được tách riêng. Gợi ý sửa cách viết không tự động khẳng định người dùng viết sai: từ có thể hợp lệ nhưng chưa nằm trong corpus. Nếu một từ hợp lệ khớp nguồn nhưng khác ý định người dùng, hệ thống không thể tự biết ý định đó.

Các âm Hán Việt được giữ đúng theo PDF. Ví dụ nhãn `丼 — TÍNH` phản ánh nội dung nguồn, chưa phải kết quả đã đối chiếu độc lập với từ điển Hán Việt. Không tự bổ sung các Kanji/âm đọc ngoài tài liệu chỉ để mở rộng danh sách tương tự.

### 7.3. Nhận dạng nét viết và dữ liệu tham chiếu

Sử dụng **454 mẫu nét KanjiVG** tương ứng 454 chữ trong corpus, revision `610091ce618cf757ed1357a8954cd65283e015d6`. SVG được chuyển thành polyline 48 điểm/nét. Nguồn và giấy phép: [KanjiVG](https://kanjivg.tagaini.net/), [repository](https://github.com/KanjiVG/kanjivg), [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Ghi công Ulrich Apel và các cộng tác viên; thay đổi và snapshot lưu trong `data/handwriting/README.md`, `artifacts/kanjivg_snapshot.json`.

Chuẩn hóa bounding box giữ tỉ lệ vào ảnh 64×64; so khoảng cách chamfer đối xứng, so từng nét sau lấy mẫu lại theo độ dài, ghép nét bằng thuật toán assignment và dùng số nét làm mức phạt mềm. Cách so khớp không bắt buộc đúng thứ tự nét; thiếu/thêm nét có thể vẫn đưa chữ mong muốn vào danh sách ứng viên. Khi điểm hình dạng chưa rõ, UI yêu cầu người dùng chọn thay vì tự xác nhận chữ đúng.

Đây là **so khớp hình dạng**, không phải mô hình OCR thần kinh hoặc công cụ chấm viết đúng/sai. Chỉ có 454 chữ nguồn. Mẫu bị nhiễu/thiếu nét trong unit test là kiểm tra chức năng tổng hợp, không phải benchmark độ chính xác trên chữ viết người thật. Sửa từ đã gõ bằng Kanji dùng độ gần chuỗi; so hình dạng glyph phụ thuộc font Nhật được cài trên máy. Hai chức năng này khác với nhận dạng nét vẽ trên canvas.

### 7.4. Phân biệt UI với benchmark lab

Benchmark A/B/C ở mục 3–6 giữ nguyên corpus, câu hỏi, config và số liệu đã khóa trước test. **Không chạy lại hoặc lấy các sửa đổi UI để thay số liệu benchmark cũ.** Chức năng từ khớp, Hán Việt, xử lý không dấu, gợi ý viết sai và nhận dạng canvas là lớp ứng dụng bổ sung; các chức năng này chưa có chỉ số Hit@1/Hit@3 hoặc độ chính xác riêng trên tập người dùng độc lập.

UI dùng collection `kanji_ui_mnemonics` cho tìm cách nhớ, gồm 454 mục, cùng model semantic đã dùng trong lab. Chỉ số của collection này không nằm trong bảng so sánh A/B/C. Collection `kanji_ui_vocabulary` từng được tạo trong quá trình thử UI hiện không được dùng trong luồng tìm kiếm cuối. Các bản lưu local có thể còn collection đó; không xem nó là chiến lược thứ tư hoặc số liệu thí nghiệm đã đánh giá.

Những vấn đề phát hiện khi dùng thử và cách xử lý:

- UI ban đầu luôn bổ sung top-3 vector nên có thể trộn mục không liên quan vào tra từ. Đã đổi sang đối chiếu từ và tách phần tương tự.
- Tra Hán Việt ban đầu phân biệt dấu quá chặt. Đã mở rộng nhóm không dấu và ưu tiên đúng dấu của input lên đầu.
- Model nhận trực tiếp `cay thong` có thể xếp hạng kém hơn `cây thông`. Đã thêm đối chiếu nghĩa và mẹo nhớ không dấu trước vector; không tuyên bố model đã được fine-tune hoặc giải quyết mọi cách diễn đạt.

### 7.5. Kiểm chứng và minh chứng

Lần kiểm tra mới nhất: **27/27 unit test qua**, log `results/ui_tests.log`. Bao phủ kiểm tra corpus/gold, ranh giới evidence, Qdrant filter/reload, một ô viết, ứng viên khi thiếu nét, input không hợp lệ, từ khớp, gợi ý sửa, nhóm âm Hán Việt và thứ tự đúng dấu, nghĩa/mô tả không dấu, phạm vi bài học. Trong đó có kiểm tra nhiều cụm nguồn: lấy mỗi trang mục thứ 25 trong 454 entry, đối chiếu nghĩa từ đầu và mẹo nhớ sau bỏ dấu. Đây là kiểm tra hồi quy trên nguồn đã biết, không phải holdout độc lập.

Đã kiểm tra bằng trình duyệt: viết `井` bằng chuột, chọn ứng viên và tra về trang 4; hoàn tác/xóa; tra `砂丘` với bài16; `TỈNH` ưu tiên `井`, `省`; `資額` có gợi ý sửa; `cay thong` trả `松`; `giong cai gieng` trả `井`. Những lần thử này là minh chứng chức năng, không phải đánh giá định lượng chất lượng mọi truy vấn.

Ảnh minh chứng:

- [UI một ô chữ mễ](../../results/ui-single-cell.png).
- [Ưu tiên Hán Việt đúng dấu](../../results/ui-tone-priority.png).
- [Tra cây thông không dấu](../../results/ui-unaccented-search.png).

Ảnh có thể được chụp ở các lần thử trước đó; bằng chứng hiện trạng code được kiểm tra cùng log test mới nhất. Hướng dẫn dùng thử cho sensei: `docs/SENSEI_DEMO.md`. Chưa ghi nhận phản hồi đánh giá độc lập từ sensei.

Chạy UI từ root dự án:

```bash
source .venv/bin/activate
python -m src.web --port 8766
```

Mở `http://127.0.0.1:8766`. Trên macOS có thể chạy `MoGiaoDienKanji.command`. Dừng server bằng Ctrl+C trước khi chạy lại build/benchmark/CLI có truy cập cùng Qdrant để tránh khóa database. Lần đầu cần chuẩn bị model/PDF; dữ liệu mẫu nét đã có tại `data/handwriting/templates.json`, có thể tái tạo bằng `python -m src.download_handwriting`.


### 7.6. Rà soát cuối và xử lý truy vấn không dấu ngoài nguyên văn

Đối chiếu không dấu đơn thuần chỉ giải quyết tốt các cụm đã có trong nguồn. Với truy vấn diễn đạt khác như `cay nhieu la`, UI hiện bổ sung **mở rộng các biến thể có dấu trước embedding**. Từ điển biến thể được thống kê từ nghĩa và mẹo nhớ trong corpus; tạo tối đa 8 phương án theo tần suất, kèm input gốc, giữ các dấu người dùng đã gõ. Các phương án dùng cùng E5 và Qdrant; chọn danh sách theo điểm top1 cao nhất. Không dùng API/LLM để khôi phục dấu, không fine-tune model, không có ánh xạ viết riêng cho từng câu thử.

Đây là heuristic: một biến thể có điểm cao không bảo đảm đúng ngữ pháp hoặc đúng dấu người dùng định nhập. Ví dụ lần kiểm tra `cay nhieu la` chọn biến thể `cây nhiều là`, vẫn trả `松` ở top1; top2/top3 khác truy vấn có dấu `cây nhiều lá`. Vì vậy chỉ xác nhận hai truy vấn có cùng top1 ở trường hợp đã thử, không tuyên bố thứ hạng luôn giống nhau hoặc khôi phục dấu hoàn hảo.

Rà soát cuối gồm **27 unit test** và **13 trường hợp API với model E5/Qdrant thật**, tất cả qua. Bộ API kiểm tra tra chữ, sửa từ chưa khớp, nhóm Hán Việt/ưu tiên dấu, cặp câu có dấu/không dấu, ngữ nghĩa diễn đạt lại, mẹo nhớ, filter bài, một ô nhận dạng, input không hợp lệ và giới hạn truy cập. Script chạy lại: `python scripts/check_ui.py` khi server đang hoạt động. Kết quả và biến thể đã chọn lưu tại `results/final_ui_checks.json`; log unit test tại `results/ui_tests.log`. Đây là kiểm tra hồi quy chức năng, không dùng thay 20 câu benchmark đã khóa hoặc human audit.

## 8. Tái lập, giới hạn và phần học viên cần xác nhận

Chạy theo README: tạo venv, cài requirements.lock.txt (bản macOS/CPU đã chạy), nhận PDF đúng hash, download model đúng revision, ingest, build, benchmark, xuất packet audit. Môi trường khác có thể cài requirements.txt rồi ghi phiên bản mới. `python -m unittest discover -s tests -v` kiểm tra corpus/gold, ranh giới evidence, bảo toàn chunk và Qdrant reload/filter. Demo UI: `python -m src.web --port 8766` hoặc `MoGiaoDienKanji.command`; CLI vẫn có `python -m src.run interactive`.

Kết quả chính: `results/metrics.csv`, `ingestion_stats.json`, `runtime.json`, `selection.json`; trace đầy đủ `results/private/traces.jsonl` (60 lượt truy xuất, 180 chunk), summary bỏ text `results/retrieval_summary.jsonl`. Nhãn AI và lý do: `ai_coherence_review.jsonl`, `ai_grounding_review.jsonl`. Metadata: `metadata_audit.jsonl`. Packet đọc: `results/private/REVIEW_PACKET.md`. Nhật ký giả thuyết: `artifacts/experiment_log.csv`.

**Cần học viên làm trước khi nộp:** đọc packet, chấm/xác nhận 30 coherence, 15 grounding và 45 metadata record; điền `student_coherence_review.csv`, `student_grounding_review.csv`, `student_metadata_review.csv`, rồi chạy `python -m src.finalize_review`. Học viên chịu trách nhiệm giải thích code/kết quả. Link repo đã được học viên nộp trên LMS. Bản cập nhật được chốt bằng tag `day06-submission-2026-11-13`; xem STUDENT.md.

Giới hạn: test chỉ 5 câu, cùng một tài liệu/template nên có rò rỉ từ vựng và thiên lệch câu tra từ; gold/AI audit cùng một trợ lý nên không độc lập. Chưa kiểm chứng toàn bộ kiến thức tiếng Nhật, nhận dạng viết tay mới kiểm tra chức năng, chưa có benchmark chữ viết người thật, chưa đánh giá định lượng câu không có đáp án, độ chính xác gợi ý sửa và mọi cách hỏi khác hoặc nguồn tương đương khác diễn đạt. Mẫu 100% test không chứng minh hệ thống đúng mọi câu; cosine luôn trả nearest chunks dù không liên quan. Chưa thu góp ý thực tế từ sensei. Nếu mở rộng: benchmark lớn hơn, người chấm độc lập, thêm exact-word/hybrid có đối chứng dev/test mới, kiểm tra glyph và các ô âm đọc thiếu.

Không phát sinh chi phí API trả phí. Tải thư viện/model dùng mạng; nội dung PDF không gửi embedding API. Các log lỗi setup/runtime được lưu; không fallback sang mock.
