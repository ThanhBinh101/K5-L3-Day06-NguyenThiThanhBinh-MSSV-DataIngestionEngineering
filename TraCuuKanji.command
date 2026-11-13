#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  print 'Cần cài môi trường theo README.md trước khi dùng.'
  read '?Nhấn Enter để đóng...'
  exit 1
fi
.venv/bin/python -m src.run interactive
read '?Nhấn Enter để đóng...'
