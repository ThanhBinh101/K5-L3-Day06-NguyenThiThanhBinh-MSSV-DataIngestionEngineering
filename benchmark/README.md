# Benchmark cố định trước truy xuất

20 câu do Codex hỗ trợ soạn, 15 dev thuộc bài 01-12, 5 test thuộc bài 13-16. Có câu hỏi trực tiếp, diễn đạt lại, phân biệt nghĩa và 7 câu yêu cầu bài học cụ thể (5 dev, 2 test). Filter `lesson` lấy từ chính câu hỏi, không lấy từ gold page hoặc đáp án.

`questions.jsonl`: câu hỏi, đáp án, raw evidence, canonical evidence, mọi trang có evidence giống nhau, split và filter. `frozen.json`: thời điểm và hash của câu hỏi, cấu hình và corpus **trước lần truy xuất đầu**. Mã kiểm tra hash trước build/benchmark và không cho ghi đè benchmark đã freeze.

Evidence raw được kiểm tra nằm trên trang PDF sau NFC và gộp khoảng trắng. Canonical evidence chỉ thay cấu trúc trình bày thành nhãn/`|`; đối chiếu sau bỏ `|` và gộp khoảng trắng. Q01 dùng tên trường Onyomi/Kunyomi đã chuẩn hóa; raw quote vẫn lưu nguyên các nhãn nguồn On yomi/Kun yomi.

Hit@1/3 yêu cầu **một chunk** đúng nguồn, đúng một trang gold hợp lệ và chứa **toàn bộ** canonical evidence theo thứ tự. Không hợp các mảnh từ nhiều chunk để đạt hit. Dùng mẫu số 15 hoặc 5. Một số đáp án có thể có nguồn tương đương với cách diễn đạt khác; người chấm có thể xác nhận thêm, nhưng phải cập nhật nhãn tương đương công khai và không tinh chỉnh chiến lược theo test.

Tiêu chí chọn: ưu tiên dev Evidence Hit@3, rồi Hit@1, rồi ít chunk; nếu bằng nhau ưu tiên B, C, A. Chốt `results/selection.json` trước khi truy xuất test. Không sửa tham số sau xem test.

Giới hạn: cùng một PDF, cùng template, mẫu nhỏ, nhiều câu tra từ; việc tách bài không loại bỏ trùng từ vựng/ngữ nghĩa. Đây là benchmark minh họa trên corpus này, không phải kiểm tra khả năng tiếng Nhật tổng quát. Codex soạn/chạy/chấm hỗ trợ, học viên cần kiểm tra gold và phần chấm thủ công trước khi nộp.
