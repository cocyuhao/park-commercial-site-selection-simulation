#!/usr/bin/env bash
# =============================================================================
# setup.sh — Codex / CI 环境初始化脚本
# 在 Linux 容器（Ubuntu 22.04+）中自动运行，Windows 用户跳过此脚本
# =============================================================================
set -euo pipefail

echo "=== 公园商业选址仿真项目 · 环境初始化 ==="
echo "Python: $(python3 --version 2>&1)"

# ---------- 1. 创建并激活虚拟环境 ----------
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/5] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "[1/5] 虚拟环境: $VIRTUAL_ENV"

# ---------- 2. 升级 pip ----------
echo "[2/5] 升级 pip..."
pip install --quiet --upgrade pip

# ---------- 3. 安装全部依赖 ----------
echo "[3/5] 安装 requirements.txt..."
pip install --quiet -r requirements.txt

# ---------- 4. 建立 .env（仅当不存在时从模板复制） ----------
echo "[4/5] 环境变量文件..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  .env 已从 .env.example 复制 — 请手动填入真实 Key"
else
    echo "  .env 已存在，跳过"
fi

# ---------- 5. 快速自检 ----------
echo "[5/5] 自检导入..."
python3 - <<'PYCHECK'
import sys
required = [
    "fitz",       # PyMuPDF
    "pdfplumber",
    "openai",
    "pandas",
    "numpy",
    "httpx",
    "aiohttp",
    "tiktoken",
    "shapely",
    "matplotlib",
    "scipy",
    "dotenv",
    "tabulate",
    "openpyxl",
    "pptx",
    "PIL",
]
failed = []
for mod in required:
    try:
        __import__(mod)
    except ImportError:
        failed.append(mod)
if failed:
    print(f"  [WARN] 以下模块导入失败: {failed}", file=sys.stderr)
    sys.exit(1)
print(f"  全部 {len(required)} 个模块导入成功")
PYCHECK

echo ""
echo "=== 初始化完成 ==="
echo "运行脚本示例:"
echo "  source .venv/bin/activate"
echo "  python 60_model/scripts/verify_deepseek_api.py"
echo "  python 30_extraction/scripts/verify_pdf_tables.py"
