#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
printf '%s\n' '安装完成。启动界面：.venv/bin/streamlit run streamlit_app.py'
