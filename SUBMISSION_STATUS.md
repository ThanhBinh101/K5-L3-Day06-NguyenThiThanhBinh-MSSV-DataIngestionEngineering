# Tình trạng bài nộp — Kanji N2

## Đã thực hiện và có minh chứng

- [x] 454 trang nội dung hợp lệ; manifest có nguồn, quyền, page ID, số ký tự, SHA-256 và quy tắc đếm.
- [x] 20 câu gold có evidence kiểm tra trước chạy; 15 dev / 5 test, 7 câu filter (2 test).
- [x] Embedding semantic thật 384 chiều, model/revision rõ ràng; Qdrant persistent + cosine + metadata filter.
- [x] A/B/C chạy đủ; A–B thay chunking, B–C chỉ thay filter.
- [x] Lưu 60 trace top3 (180 kết quả), số liệu dev/test, thời gian, chi phí và nhãn evidence.
- [x] Đóng/mở database kiểm chứng lưu bền vững; lặp nạp không tăng số chunk.
- [x] Đã chọn B theo dev trước truy xuất test, giữ hash cấu hình/corpus/benchmark.
- [x] AI đọc mẫu và ghi nhãn/lý do cho coherence, grounding; metadata đối chiếu nguồn, ghi rõ provenance.
- [x] Báo cáo phân tích 5 khía cạnh, lỗi, đánh đổi, giới hạn; code, setup/run, experiment log.
- [x] UI một ô viết tay; tự nhận biết Kanji, nghĩa, gợi nhớ; tra Hán Việt không dấu/ưu tiên đúng dấu; gợi ý sửa và phần tương tự riêng.
- [x] 27 unit test qua, có ảnh minh chứng UI và tìm không dấu; báo cáo cập nhật phần mở rộng, tách khỏi benchmark.
- [x] Bản tra cứu tương tác và hướng dẫn dành cho sensei; nội dung chạy local.
- [x] Điền Nguyễn Thị Thanh Bình, MSSV 2A202603497, lớp L3A theo thông tin đã có/xác nhận.

## Học viên chốt trước nộp

- [ ] Đọc `results/private/REVIEW_PACKET.md`, đối chiếu PDF, điền 3 CSV `student_*_review.csv`; chạy `python -m src.finalize_review` để bổ sung kết quả học viên vào báo cáo. Nhãn AI không được ghi thành nhãn đã chấm bởi học viên.
- [ ] Kiểm tra hiểu được pipeline, metric, ví dụ lỗi và phần nguồn/quyền trước demo với giảng viên.
- [x] Học viên xác nhận đã nộp link repo trên LMS; cập nhật bản code/báo cáo và chốt tag `day06-submission-2026-11-13` trên GitHub.
- [ ] Cung cấp riêng đúng PDF cho người chấm/sensei theo quyền đã được cho phép; raw corpus và trace đầy đủ không tự động lên Git. Không có URL tải công khai đã xác minh.

Không gửi tin nhắn/tài liệu cho sensei hoặc thao tác lại LMS. Chỉ cập nhật repo đã nộp.
