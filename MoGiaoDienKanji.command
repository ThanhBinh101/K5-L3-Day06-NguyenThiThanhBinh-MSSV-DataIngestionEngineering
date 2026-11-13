#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  print 'Cần cài môi trường theo README.md trước khi dùng.'
  read '?Nhấn Enter để đóng...'
  exit 1
fi
print 'Mở http://127.0.0.1:8766 trong trình duyệt. Giữ cửa sổ Terminal này khi dùng.'
.venv/bin/python -m src.web --port 8766
read '?Nhấn Enter để đóng...'
