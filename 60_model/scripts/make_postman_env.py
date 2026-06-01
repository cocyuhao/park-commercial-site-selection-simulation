"""
make_postman_env.py
===================
从 .env 读取 DEEPSEEK_API_KEY，生成 Postman 环境文件
40_quality_evidence/postman_deepseek_env.json

用户导入步骤：
1. 打开 Postman → Import → 选 postman_deepseek_collection.json
2. 打开 Postman → Import → 选 postman_deepseek_env.json
3. 右上角选择环境 "DeepSeek 仿真设计"
4. 发送请求即可
"""
from __future__ import annotations
import json, uuid
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

key = os.environ.get("DEEPSEEK_API_KEY", "")
if not key:
    raise SystemExit("❌ .env 中未找到 DEEPSEEK_API_KEY")

env = {
    "id": str(uuid.uuid4()),
    "name": "DeepSeek 仿真设计",
    "values": [
        {"key": "base_url", "value": "https://api.deepseek.com", "enabled": True},
        {"key": "api_key",  "value": key,                         "enabled": True, "type": "secret"},
    ],
    "_postman_variable_scope": "environment",
}

out = ROOT / "40_quality_evidence" / "postman_deepseek_env.json"
out.write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ 环境文件已生成: {out}")
print()
print("Postman 导入步骤：")
print("  1. File → Import → 选 postman_deepseek_collection.json")
print("  2. File → Import → 选 postman_deepseek_env.json")
print("  3. 右上角下拉选 'DeepSeek 仿真设计'")
print("  4. 即可发送请求")
