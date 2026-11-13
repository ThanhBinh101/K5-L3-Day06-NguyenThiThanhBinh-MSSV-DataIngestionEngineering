# Corpus Kanji N2

Nguồn: `KANJI N2.pdf` do sensei của học viên biên soạn, tác giả hiển thị trong file là **Kaori Sensei**. Ngày 13/11/2026, học viên xác nhận đã được sensei cho phép sử dụng và sẽ gửi công cụ để sensei dùng thử.

PDF gốc được giữ tại `data/raw/KANJI N2.pdf`, không commit. Người chấm hoặc sensei cần dùng đúng bản PDF do học viên cung cấp riêng; kiểm tra SHA-256 trong `manifest.json`. Không có URL tải công khai được xác minh. `data/format-example.json` là ví dụ của đề, không dùng làm corpus.

Lệnh tái tạo:

```bash
python -m src.run ingest --pdf 'data/raw/KANJI N2.pdf'
```

`manifest.json` ghi từng trang, số ký tự sau NFC và gộp khoảng trắng, lý do giữ/bỏ, SHA-256, quyền sử dụng và thời gian xử lý. `processed/pages.jsonl` giữ text từng trang; `processed/entries.jsonl` giữ các mục Kanji chuẩn hóa. Các file này chỉ lưu local.

Quy tắc: tính 454 trang có nội dung học Kanji (âm đọc, cách nhớ, từ phái sinh); loại bìa, mục lục, 16 trang tổng quan bài học và trang hướng dẫn/nguồn cuối. Không tính ô luyện viết thành nội dung riêng, không nhân bản trang. Những hình minh họa/mô hình nét viết không được lập chỉ mục bởi pipeline text.

Chuẩn hóa thêm nhãn trường và dấu `|` để giữ quan hệ từ - cách đọc - nghĩa. Dấu `-` trong ô âm đọc được giữ nguyên là thiếu dữ liệu trong nguồn, không tự bổ sung kiến thức ngoài. Không suy ra toàn bộ mục từ đều thuộc JLPT N2: ghi chú cuối PDF nói có nội dung mở rộng N3/N1.

Giấy phép: quyền sử dụng cho lab theo xác nhận học viên; chưa xác minh quyền phát hành công khai toàn bộ PDF. Trang cuối ghi dữ liệu từ vựng dựa trên JMdict/EDRDG, CC BY-SA 4.0, nghĩa Việt biên soạn/rút gọn. Cần giữ ghi công khi chia sẻ dữ liệu phái sinh. Tham khảo: https://www.edrdg.org/jmdict/j_jmdict.html và https://www.edrdg.org/edrdg/licence.html. Không tự áp dụng giấy phép này cho hình ảnh hoặc toàn bộ PDF.
