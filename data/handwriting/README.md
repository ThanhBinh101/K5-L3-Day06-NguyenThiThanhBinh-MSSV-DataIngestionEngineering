# Nét mẫu KanjiVG

`templates.json` chứa nét SVG của đúng 454 Kanji trong corpus, được lấy từ KanjiVG rồi chuyển thành polyline 48 điểm/nét, làm tròn 3 chữ số. Snapshot/revision và thời gian lấy nằm trong `artifacts/kanjivg_snapshot.json`.

Nguồn: https://github.com/KanjiVG/kanjivg · https://kanjivg.tagaini.net/

Copyright © Ulrich Apel và các cộng tác viên KanjiVG. Dữ liệu nét và bản polyline phái sinh được chia sẻ theo **Creative Commons Attribution-ShareAlike 3.0**: https://creativecommons.org/licenses/by-sa/3.0/ . Giữ ghi công, ghi thay đổi và chia sẻ cùng giấy phép khi phân phối lại file dữ liệu này. Giấy phép không áp dụng tự động cho nội dung PDF của sensei hay code dự án.

Tái tạo: `python -m src.download_handwriting`. Cần mạng lần đầu; script dùng revision đã ghi nếu snapshot tồn tại. Chỉ tải dữ liệu nét công khai, không gửi PDF hoặc chữ viết của người dùng.

## Phương pháp và giới hạn

Chuẩn hóa bounding box giữ tỉ lệ vào ảnh 64×64, raster nét, tính khoảng cách chamfer đối xứng với các mẫu; số nét là một mức phạt mềm. Không yêu cầu đúng thứ tự nét. Trả về 8 ứng viên gần nhất, có thể có chữ tương tự khi thiếu/thêm nét. Đây là **shape matching**, chưa phải mô hình OCR viết tay được huấn luyện hay trình sửa chữ sai. Chỉ gợi ý trong 454 chữ có sẵn, không đoán mọi chữ Hán. Khoảng cách không phải xác suất chính xác, không tự kết luận chữ viết đúng/sai.

Kiểm tra bằng các nét mẫu bị nhiễu/thiếu nét chỉ là sanity check tổng hợp, không thay cho benchmark chữ viết của người thật. Người dùng cần chọn ứng viên và kiểm chứng nguồn; chữ viết quá biến dạng có thể không có chữ mong muốn trong top8.
