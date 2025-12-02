# services/constants.py
# ----------------------------------------------------
# 存放所有公共常量和路径配置

import os

# 路径配置
# 假设项目的根目录是 /Users/luckpuppy/Desktop/UItools/gemini
DATA_DIR = "/Users/luckpuppy/Desktop/UItools/gemini/data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 数据持久化文件定义 (使用绝对路径)
CLASSIFIED_DATA_FILE = os.path.join(DATA_DIR, "classified_data.json")
CUSTOM_KEYWORD_FILE = os.path.join(DATA_DIR, "custom_keywords.json")
HISTORY_FILE = os.path.join(DATA_DIR, "translation_history.json")

print(f"INFO: Data files will be stored in: {DATA_DIR}")