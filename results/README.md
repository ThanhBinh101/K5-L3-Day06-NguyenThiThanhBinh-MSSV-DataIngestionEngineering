# Minh chứng kết quả

## Bản chốt hiện tại

- `metrics.csv`, `metrics.json`, `ingestion_stats.json`, `selection.json`, `runtime.json`: kết quả benchmark A/B/C gốc đã chạy; không thay bằng số liệu UI.
- `ui_tests.log`: lần chạy unit test cuối, 27 test.
- `final_ui_checks.json`: 13 trường hợp truy vấn live cùng các kiểm tra nhận dạng một ô, filter và biên input; model/Qdrant thật.
- `final_review.json`: kiểm tra tính toàn vẹn corpus/benchmark, số liệu, tài liệu và danh sách file trước commit.
- `ai_coherence_review.jsonl`, `ai_grounding_review.jsonl`, `metadata_audit.jsonl`: nhãn AI/phương pháp đối chiếu nguồn có provenance. Không tự gán thành nhãn học viên.
- `student_*_review.csv`: phiếu để học viên chấm/xác nhận. Hiện để trống, chưa có kết quả human audit; báo cáo ghi rõ giới hạn này.

`tests.log`, `ui_checks.json`, `ui_lookup_checks.json`, `acceptance_checks.json` và các ảnh UI là minh chứng các mốc trước; một số phản ánh bản 8 ô hoặc số test cũ. Chúng không mô tả thay cho bản chốt một ô hiện tại. Bản hiện tại được xác định bằng code trên tag `day06-submission-2026-11-13` và `final_ui_checks.json`.

Trace đầy đủ và packet đọc chứa trích đoạn tài liệu ở `results/private/`, chỉ lưu local. Repo công khai có summary bỏ text tại `retrieval_summary.jsonl`, manifest và lệnh tái tạo. Người chấm cần nhận riêng đúng PDF từ học viên rồi chạy theo README. `ui_server.log` là log thay đổi khi dùng thử, không commit.
