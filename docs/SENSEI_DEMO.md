# Bản dùng thử dành cho sensei

Công cụ tra cứu dựa trên tài liệu **KANJI N2 - Kaori Sensei** đã được sensei cho học viên sử dụng. Mục đích: tìm nhanh mục Kanji, cách đọc, nghĩa từ phái sinh và mở đúng trang tài liệu để kiểm tra.

## Trên máy đã setup

macOS: mở `TraCuuKanji.command` từ Finder, hoặc dùng Terminal:

```bash
source .venv/bin/activate
python -m src.run interactive
```

Nhập câu hỏi bằng tiếng Việt hoặc tiếng Nhật. Ví dụ:

- `天井 đọc thế nào và nghĩa là gì?`
- `Từ nào nghĩa là giấy phép?`
- `Chữ 井 có âm đọc nào?`

Lọc bài: gõ `/bai 16`, rồi nhập `Từ nào nghĩa là đồi cát?`. Gõ `/tat` để tìm toàn bộ tài liệu; `/thoat` để kết thúc.

Mỗi lần trả về 3 đoạn, có tên nguồn, số trang PDF, bài học và điểm tương đồng cosine. Điểm này **không phải xác suất câu trả lời đúng**. Công cụ không tạo lời giải bằng LLM, không tự thêm kiến thức ngoài tài liệu. Sau khi tải model lần đầu, tra cứu và embedding hoạt động local; nội dung tài liệu không gửi tới API.

## Trên máy khác

Làm các bước cài đặt trong README, nhận riêng file PDF đúng SHA-256 từ học viên, tải model rồi chạy ingest/build. Không cần API key hoặc Docker. Không chia sẻ thư mục `.venv` giữa các hệ điều hành; cài lại từ requirements. Vector store `.local/qdrant` có thể tái tạo từ PDF.

## Góp ý đề nghị sensei kiểm tra

1. Cách đọc và nghĩa có giữ đúng so với trang nguồn không?
2. Có câu hỏi tìm không ra hoặc trả về chữ gần giống không? Ghi lại câu hỏi, số bài và kết quả mong đợi.
3. Những ô âm đọc nguồn ghi `-` cần được giữ là chưa có dữ liệu; công cụ không tự bổ sung.
4. Mẹo nhớ là nội dung học tập của tài liệu, không phải giải thích từ nguyên đã được công cụ xác thực.

Để trao đổi: học viên tổng hợp góp ý trực tiếp với sensei; công cụ không có tính năng gửi nội dung ra ngoài. Chưa thực hiện gửi/tải lên công khai tài liệu.

## Giao diện viết tay và tra cứu tự động

Chạy `python -m src.web --port 8766`, mở http://127.0.0.1:8766 hoặc mở launcher `MoGiaoDienKanji.command`. Một ô tìm kiếm chung tự phân biệt Kanji, nghĩa và cách gợi nhớ. Tra âm Hán Việt (ví dụ TỈNH) trả các Kanji đồng âm có trong nguồn. Nếu chữ/từ không khớp, có gợi ý “Có phải bạn muốn tìm?”; từ/chữ tương tự nằm ở phần Lưu ý riêng. Có thể nhấp gợi ý để tìm lại.

Chỉ **một ô chữ mễ**: viết một chữ bằng chuột/bút/cảm ứng, chọn trong 8 ứng viên rồi Tra cứu chữ này. Hỗ trợ hoàn tác và xóa. Gợi ý hình dạng không phải xác nhận đúng/sai. Mẹo nhớ ví dụ “Cái giếng 2 tầng” tìm 井; công cụ dùng đúng nội dung mẹo nhớ của tài liệu.

PDF và nét viết xử lý tại máy. Chưa có tính năng gửi/chia sẻ tự động. Tắt server trước chạy lại pipeline/benchmark do database local có khóa riêng.

Tra nghĩa và gợi nhớ chấp nhận không dấu: `cay thong`, `mien thue`, `giong cai gieng`. Với câu diễn đạt khác nguồn như `cay nhieu la`, hệ thống thử thêm biến thể có dấu trước model; kết quả vẫn cần đối chiếu. Hán Việt không dấu trả nhóm âm tương tự, âm đúng dấu input được ưu tiên lên đầu.
