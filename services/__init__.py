# services/__init__.py (修改内容)

# 1. 导入常量和打印信息 (只导入 DataModel 需要的，或全部导入用于调试)
from gemini.services.constants import (
    CLASSIFIED_DATA_FILE, CUSTOM_KEYWORD_FILE, HISTORY_FILE, DATA_DIR
)
print(f"INFO: Data files will be stored in: {DATA_DIR}") # 重新添加打印信息

# 2. 桥接内部类 (保持不变)
from gemini.services.data_model import DataModel
from gemini.services.analysis_service import QingShiluService
from gemini.services.file_manager import FileManager