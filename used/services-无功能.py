# services-未拆分.py
# 核心业务逻辑层：负责数据处理、算法调用和核心文件操作

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


class AnalysisService:
    """处理文本分析相关的核心业务逻辑：智能分析、翻译生成等。"""

    def __init__(self):
        # 实际项目中，这里会初始化 BERT 模型、词库加载、数据库连接等核心资源
        pass

    def analyze_text(self, text: str) -> str:
        """接收原文，返回智能翻译和分类结果（模拟）"""
        if not text:
            # 业务逻辑层不处理 UI 消息，仅返回状态或数据
            return ""

        # ----------------------------------------------------
        # 实际的 BERT/NLP 模型调用、复杂算法、数据库查询等核心逻辑在这里实现
        # ----------------------------------------------------

        translation_text = (
            f"【原文】\n{text}\n\n"
            f"【智能翻译（Service层生成）】\n这是对原文的白话文翻译和智能分类结果。"
        )
        return translation_text


class FileManager:
    """处理文件操作相关的核心业务逻辑：选择文件、批量处理调度等。"""

    def __init__(self):
        self.selected_files = []  # 存储当前选中的文件列表 (数据状态)

    def select_batch_files(self, parent_widget: QWidget) -> list[str] | None:
        """打开文件对话框，选择文件列表，并更新内部状态"""
        # 注意：QFileDialog 属于 UI 交互，但由于它是文件系统的入口，通常在服务层进行封装。
        files, _ = QFileDialog.getOpenFileNames(
            parent_widget, "选择批量文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if files:
            self.selected_files = files
            return files

        # 如果用户取消选择，清空状态
        self.selected_files = []
        return None

    def get_selected_files(self) -> list[str]:
        """获取当前选中的文件列表"""
        return self.selected_files

    def process_files(self):
        """执行批量分析的核心调度逻辑"""
        files_to_process = self.get_selected_files()
        if not files_to_process:
            # 在没有文件时，不执行核心逻辑，并返回
            return

        # ----------------------------------------------------
        # 实际的批量读取文件、循环调用 AnalysisService、写入输出文件等逻辑在这里实现
        # ----------------------------------------------------
        print(f"Service: 开始处理 {len(files_to_process)} 个文件...")
        # 模拟长时间运行后反馈
        QMessageBox.information(None, "批量分析",
                                f"Service: 开始执行 {len(files_to_process)} 个文件的核心分析，分析完成！")