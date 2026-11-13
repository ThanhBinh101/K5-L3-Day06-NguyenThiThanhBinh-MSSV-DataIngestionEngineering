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
