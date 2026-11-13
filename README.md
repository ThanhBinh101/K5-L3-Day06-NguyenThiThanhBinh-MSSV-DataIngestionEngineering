# Day 6 — Tra cứu Kanji N2

**Nguyễn Thị Thanh Bình · 2A202603497 · L3A**

Pipeline Python xử lý toàn bộ 454 trang học Kanji trong PDF 473 trang, tạo semantic embedding thật, lưu Qdrant local và trả về top-3 đoạn có nguồn/trang. So sánh ba chiến lược A/B/C trên cùng corpus/model và benchmark đã khóa 15 dev + 5 test. Không cần API key hoặc Docker.

## Kết quả đã chạy

| Cấu hình | Chunk | Dev Hit@1 | Dev Evidence Hit@3 | Test Hit@1 / Hit@3 |
|---|---:|---|---|---|
| A — cửa sổ 220/40 | 774 | 12/15 | 13/15 | 5/5 · 5/5 |
| B — trọn mục Kanji | 454 | 13/15 | 15/15 | 5/5 · 5/5 |
| C — B + lọc bài | 454 | 13/15 | 15/15 | 5/5 · 5/5 |

Chọn **B theo dev trước khi chạy test**. C hỗ trợ chọn phạm vi bài học cho demo. Tập test chỉ 5 câu, kết quả không bảo đảm đúng mọi câu hỏi. Đọc [báo cáo](report/individual/2A202603497_NguyenThiThanhBinh.md), [số liệu](results/metrics.csv) và [hướng dẫn cho sensei](docs/SENSEI_DEMO.md).

**Trạng thái bài:** code, corpus local, benchmark, trace, kết quả và báo cáo đã có. Nhãn AI được ghi rõ; phần học viên chấm/xác nhận còn để trống theo yêu cầu trung thực của đề. Link repo đã được học viên nộp trên LMS; bản cập nhật được chốt bằng tag `day06-submission-2026-11-13`.

## 1. Cài đặt

Python 3.11+ (máy đã chạy Python 3.12, macOS ARM64). Terminal tại thư mục dự án:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
```

`requirements.lock.txt` ghi chính xác các bản đã chạy. Trên nền tảng khác, nếu wheel không tương thích, dùng `python -m pip install -r requirements.txt`, sau đó ghi lại `pip freeze` cho thí nghiệm mới. Model và thư viện cần mạng lần đầu.

## 2. Chuẩn bị dữ liệu và model

Nhận riêng PDF từ học viên/sensei và đặt tại `data/raw/KANJI N2.pdf`. Bản local hiện tại đã có. Kiểm tra SHA-256 theo `data/manifest.json` nếu chuyển máy. PDF, corpus trích xuất, model và database không commit. Quyền sử dụng: sensei biên soạn và cho học viên dùng làm lab/gửi dùng thử, theo xác nhận học viên; chưa xác minh quyền đăng công khai toàn bộ PDF.

```bash
python -m src.download_model
python -m src.run ingest --pdf 'data/raw/KANJI N2.pdf'
```

Model: `intfloat/multilingual-e5-small`, 384 chiều, revision được khóa trong `artifacts/model_snapshot.json`. Mọi embedding chạy CPU local, prefix `passage: `/`query: `, L2 normalization, cosine. Không gửi nội dung PDF tới API. Attribution và đếm trang: [data/README.md](data/README.md).

## 3. Build và benchmark

```bash
python -m src.run build
python -m src.run benchmark
python -m unittest discover -s tests -v
```

Build khởi tạo **chỉ các collection lab `kanji_A/B/C`** trong `.local/qdrant`, ghi vector, lặp upsert kiểm tra nạp lại không trùng, đóng/mở lại để xác minh lưu bền vững. C dùng lại vector B. Nếu PDF đổi, build thay collection để xóa chunk cũ; dữ liệu thay đổi cần benchmark/thí nghiệm mới.

Benchmark và cấu hình đã khóa hash. `src.prepare_benchmark` chỉ dùng khi tạo benchmark lần đầu, chủ động từ chối ghi đè `benchmark/frozen.json`. Không xóa khóa để sửa test sau khi đã nhìn kết quả. Khi làm thí nghiệm mới, lưu riêng bản cũ và tạo tập test mới trước truy xuất. Không chạy benchmark để “tune” trên test hiện tại.

Chạy lại cùng inputs kiểm chứng tái lập, không tạo holdout mới. Số liệu thời gian sẽ khác giữa các lần chạy. Không đổi chiến lược đã chốt dựa vào test.

## 4. Tra cứu cho sensei

```bash
python -m src.run search '天井 đọc thế nào và nghĩa là gì?'
python -m src.run search 'Từ nào nghĩa là đồi cát?' --strategy C --lesson 16
python -m src.run interactive
```

macOS có thể mở `TraCuuKanji.command`. Trong chế độ tương tác: `/bai 16` lọc bài; `/tat` bỏ lọc; `/thoat` đóng. Kết quả gồm text, nguồn, số trang, bài và cosine. Cosine không phải độ tin cậy xác suất; cần đọc đoạn nguồn, đặc biệt khi câu hỏi không có đáp án. Dấu `-` ở âm đọc được giữ như nguồn.

## 5. Chấm/xác nhận thủ công trước nộp

Packet đã có tại `results/private/REVIEW_PACKET.md` (chứa toàn bộ đoạn cần đọc). Code xuất lại packet khi cần:

```bash
python -m src.audit
```

Lệnh giữ nguyên các CSV student đã tồn tại; nhãn AI riêng trong `results/ai_*_review.jsonl`. Học viên đọc packet đối chiếu PDF rồi điền:

- `results/student_coherence_review.csv`: 30 dòng, điểm 0/1/2, lý do, người chấm, ngày.
- `results/student_grounding_review.csv`: 15 dòng, điểm 0/1/2 và các trường trên.
- `results/student_metadata_review.csv`: 45 dòng, đúng/đủ 0/1, lý do, người chấm, ngày.

```bash
python -m src.finalize_review
```

Lệnh từ chối nhãn trống, thiếu dòng hoặc dòng bị đổi; không tự chép điểm AI. Khi đủ, tạo `student_audit_summary.json` và bổ sung bảng nhãn học viên vào báo cáo. Báo cáo tạm thời minh bạch phần AI hỗ trợ, chưa giả là human audit. Nếu chỉ cập nhật trình bày báo cáo: `python -m src.report`.

## Cấu trúc và minh chứng

```text
src/                   ingestion, chunking, embedding, Qdrant, evaluation, CLI, audit
configs/               3 cấu hình và tiêu chí chọn
benchmark/             20 câu, gold evidence, split và frozen hashes
artifacts/             giả thuyết A/B/C, model revision
results/               metric, stats, logs, audit, CSV học viên
results/private/       trace text và packet đọc (local)
data/manifest.json     nguồn, quyền, hash, tất cả page ID và số ký tự
data/raw/              PDF gốc (local)
data/processed/        pages, entries, chunks (local)
.local/                model, cache, Qdrant (local)
report/individual/     báo cáo cá nhân
```

Trace có 60 lượt truy xuất, mỗi lượt top3 gồm ID, text, score, metadata và nhãn evidence. Bản summary bỏ text ở `results/retrieval_summary.jsonl`. `runtime.json` ghi phiên bản, model, seed, metric, provider local và chi phí $0 API. Các giới hạn, lỗi font, lỗi truy xuất và đánh đổi được ghi trong báo cáo.

**Tài liệu đề gốc:** [README gốc](docs/LAB_ORIGINAL.md), [GUIDE](GUIDE.md), [BENCHMARK](BENCHMARK.md), [RUBRIC](RUBRIC.md), [quy tắc](RULES.md), [bài nộp](SUBMISSION.md). Starter pgvector là mẫu của đề, không phải đường chạy bài này; triển khai hoàn chỉnh dùng `src/` + Qdrant.

## UI tra cứu và một ô viết tay

```bash
source .venv/bin/activate
python -m src.web --port 8766
```

Mở **http://127.0.0.1:8766**. macOS có launcher `MoGiaoDienKanji.command`. Một ô tìm kiếm chung, tự nhận biết input, không cần chọn chế độ:

- **Kanji / cách đọc:** tìm chữ/từ khớp. Nếu không khớp, hiện “Có phải bạn muốn tìm?” với các từ gần cách viết. Với một chữ, có thêm so hình dạng bằng font Nhật local. Mục “Lưu ý: từ tương tự” nằm riêng, không trộn vào kết quả chính. Từ hợp lệ vẫn có thể khác từ người dùng định viết; công cụ không tự phán là sai.
- **Âm Hán Việt:** trả tất cả Kanji có cùng âm Hán Việt khi bỏ dấu trong tài liệu và phạm vi bài đã chọn; ví dụ TỈNH có 井 và 省. Không phân biệt dấu hoặc hoa/thường: Tinh, TÍNH, TỊNH cùng tìm nhóm TINH/TÍNH/TÌNH/TỊNH/TỈNH/TĨNH có trong tài liệu; tên từng kết quả vẫn giữ đúng dấu.
- **Ngữ nghĩa:** tìm các mục gần nghĩa bằng embedding và Qdrant. Không dùng index từ mở rộng của thử nghiệm trước. Kết quả gần nghĩa cần được đối chiếu.
- **Cách gợi nhớ / miêu tả:** tìm trên mẹo nhớ của 454 chữ bằng một collection riêng. Cụm khớp trực tiếp được ưu tiên; ví dụ “Cái giếng 2 tầng” → 井. Đây là tìm trong cách nhớ của tài liệu, không phải phân tích từ nguyên/chấm cấu tạo chữ.

Phần viết tay giới hạn **1 ô chữ mễ**, mỗi lần một chữ. Vẽ bằng chuột/bút/cảm ứng; tự nhận dạng sau khi thả bút hoặc bấm Nhận dạng. Có hoàn tác, xóa và 8 **ứng viên** gần giống (không phải 8 ô). Chọn ứng viên rồi bấm Tra cứu chữ này. Nét viết chạy local, không lưu hoặc gửi ra ngoài. KanjiVG chỉ gồm 454 chữ nguồn; ghi công CC BY-SA 3.0 trong data/handwriting/README.md.

Phần mở rộng UI tách khỏi benchmark A/B/C đã khóa. Kết quả sửa lỗi/chữ viết tay chưa có benchmark người thật. Chỉ gợi ý từ có trong tài liệu, không khẳng định từ người dùng gõ là sai nếu không khớp. Tắt server bằng Ctrl+C trước chạy lại build/benchmark/CLI để tránh khóa Qdrant.

Kiểm tra `python -m unittest discover -s tests -v`: 27 test, gồm một ô nhận dạng, từ khớp, từ chưa có không tự tách thành chữ, gợi ý sửa và toàn bộ Kanji đồng âm Hán Việt.

Tra âm Hán Việt ưu tiên khớp đúng dấu đã nhập; nhóm âm tương tự xếp bên dưới với tiêu đề riêng. Ví dụ TỈNH: 井 và 省 trước, các biến thể TINH/TÍNH/TÌNH/TỊNH sau.

Ngữ nghĩa và gợi nhớ có đối chiếu nội dung nguồn không phân biệt dấu trước khi gọi vector: “cay thong” → 松, “mien thue” → 免, “cai gieng 2 tang” / “giong cai gieng” → 井. Giữ nguyên văn bản có dấu trong kết quả. Những mô tả chưa khớp nguồn vẫn dùng vector và cần đối chiếu, không bảo đảm mọi cách diễn đạt đều đúng.

Rà soát bản chốt: **27 unit test + 13 trường hợp API với model/Qdrant thật**. Chạy lại API khi server đang hoạt động bằng `python scripts/check_ui.py`; output ở `results/final_ui_checks.json`. Truy vấn ngoài nguyên văn không dấu được mở rộng tối đa 8 biến thể có dấu dựa trên corpus, kèm input gốc trước embedding. Ví dụ cây nhiều lá/cay nhieu la đều có 松 ở top1 trong lần thử; các vị trí sau có thể khác. Đây là heuristic, không bảo đảm khôi phục dấu đúng mọi câu.
