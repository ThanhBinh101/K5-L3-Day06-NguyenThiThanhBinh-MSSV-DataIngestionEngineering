# Nhật ký setup và giới hạn môi trường

- 13/11/2026, Asia/Ho_Chi_Minh: pip trong sandbox không phân giải được pypi; lần cài đầu thất bại, chưa tạo embedding/kết quả.
- Thực hiện lại cài thư viện có quyền truy cập mạng; thành công. Phiên bản thực tế lưu requirements.lock.txt và runtime.json.
- Tải multilingual-e5-small công khai từ Hugging Face theo revision trong artifacts/model_snapshot.json. Không sử dụng key hoặc API trả phí; không gửi nội dung PDF lên Hugging Face.
- Không dùng model/vector mock để thay thế khi lỗi. Các vector tổng hợp trong một unit test chỉ kiểm tra semantics filter/idempotent của database, tách khỏi pipeline và số liệu lab.
- Đọc PDF ban đầu bằng pypdf bundled, sau đó chạy lại ingestion bằng pypdf 7.0.1 trong venv đã khóa; hash corpus/benchmark vẫn hợp lệ.
- pypdf báo CMap hex độ dài lẻ (có các mã Unicode bổ sung) lặp trên các trang; giữ đầy đủ extraction_warnings.log. Không có lỗi parser/trang rỗng, đủ 454 entry/1764 từ, nhưng không suy ra mọi glyph đã được kiểm tra.
- Model embedding chạy CPU; Qdrant local báo exact search mặc định, search_params không thay đổi thuật toán local. Không có dịch vụ PostgreSQL/Qdrant server cần dựng.
- Nhãn AI được đọc từ packet và lưu minh bạch; không tạo nhãn học viên. Hai bảng điểm và metadata review của học viên chờ điền.
