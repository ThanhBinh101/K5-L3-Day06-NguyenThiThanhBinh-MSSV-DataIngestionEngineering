"""Add the current UI implementation without changing frozen benchmark results."""
from .common import ROOT


def update_report(text):
    text=text.replace('**Lớp:** L2A','**Lớp:** L3A')
    text=text.replace('chưa tìm theo ảnh/nét viết','nhận dạng viết tay mới kiểm tra chức năng, chưa có benchmark chữ viết người thật')
    text=text.replace('chưa đánh giá câu không có đáp án, lỗi gõ, mọi cách hỏi khác','chưa đánh giá định lượng câu không có đáp án, độ chính xác gợi ý sửa và mọi cách hỏi khác')
    text=text.replace('Có thể thử exact-word/hybrid trong thí nghiệm mới, chưa triển khai hoặc đo ở đây.',
        'UI đã bổ sung ưu tiên từ khớp để xử lý trải nghiệm này; chưa đo tác động đó bằng benchmark mới. Hybrid vẫn là hướng mở rộng.')
    text=text.replace('Demo: `python -m src.run interactive` hoặc `TraCuuKanji.command`.',
        'Demo UI: `python -m src.web --port 8766` hoặc `MoGiaoDienKanji.command`; CLI vẫn có `python -m src.run interactive`.')
    text=text.replace('## 8. Nhãn học viên đã xác nhận','## 9. Nhãn học viên đã xác nhận')
    marker='## 7. Tái lập, giới hạn và phần học viên cần xác nhận'
    if marker in text:
        extension=(ROOT/'report/UI_IMPLEMENTATION.md').read_text(encoding='utf-8').strip()
        text=text.replace(marker,extension+'\n\n## 8. Tái lập, giới hạn và phần học viên cần xác nhận')
    return text
