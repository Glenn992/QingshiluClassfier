# services/file_manager.py
# ----------------------------------------------------
# FileManager 类：文件I/O、批量处理、UI交互

import os
import re
from PySide6.QtWidgets import QFileDialog, QWidget

# 从同级模块导入 QingShiluService (用于分析)
from gemini.services.analysis_service import QingShiluService


class FileManager:
    """
    负责文件操作相关的核心业务逻辑，现包含多条历史条文的批量处理。
    """

    def __init__(self, qingshilu_service: QingShiluService):
        self.qingshilu_service = qingshilu_service
        self.selected_files = []
        # 存储批量分析结果，包含条文的列表
        self.batch_articles = []

    def select_batch_files(self, parent_widget: QWidget) -> list[str] | None:
        """打开文件对话框，选择文件列表，并更新内部状态"""
        files, _ = QFileDialog.getOpenFileNames(
            parent_widget, "选择批量文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if files:
            self.selected_files = files
            return files

        self.selected_files = []
        return None

    def get_selected_files(self) -> list[str]:
        """返回当前选中的文件列表"""
        return self.selected_files

    def _split_text_into_articles(self, text: str, file_name: str) -> list[dict]:
        """
        根据“○”或“○+序号”的特征，将文本拆分成多条历史条文。
        """

        # 在文本开头强制添加一个标记，以便捕获第一个条文
        temp_text = "\n○1 " + text.strip()

        # 使用 finditer 找到所有匹配的条文块
        articles_re_match = re.finditer(r"(\n[ \t]*)(○\d*\s*)(.*?)(?=\n[ \t]*○\d*\s*|\Z)", temp_text, re.DOTALL)

        final_articles = []
        article_index = 1

        for match in articles_re_match:
            # group(2) 是 ○编号, group(3) 是条文内容
            article_content = (match.group(2) + match.group(3)).strip()

            # 为每条条文生成一个唯一ID：文件名_序号
            article_id = f"{os.path.basename(file_name).split('.')[0]}_{article_index}"

            final_articles.append({
                "article_id": article_id,
                "originalText": article_content
            })
            article_index += 1

        return final_articles

    def process_files(self):
        """
        执行批量分析的核心调度逻辑：读取文件 -> 拆分条文 -> 分析条文。
        """
        files_to_process = self.get_selected_files()
        if not files_to_process:
            return "错误：没有文件可供处理。"

        self.batch_articles = []
        total_files = len(files_to_process)
        article_count = 0

        for i, file_path in enumerate(files_to_process):
            try:
                # 1. 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()

                # 2. 拆分文件为多条历史条文
                articles = self._split_text_into_articles(text, file_path)
                article_count += len(articles)

                # 3. 对每条条文进行分析
                for article in articles:
                    # 调用核心分析服务进行分析
                    analysis_result = self.qingshilu_service.run_full_analysis(article['originalText'])

                    self.batch_articles.append({
                        "article_id": article['article_id'],
                        "originalText": article['originalText'],
                        "analysis": analysis_result,
                        "classification_key": None  # 初始时未分类
                    })

                print(
                    f"Service: 批量处理文件 {os.path.basename(file_path)} 完成，拆分出 {len(articles)} 条条文 ({i + 1}/{total_files})")

            except Exception as e:
                error_msg = f"处理文件 {os.path.basename(file_path)} 失败: {e}"
                print(error_msg)
                # 记录文件级别的错误 (将错误作为单独的条目记录)
                self.batch_articles.append({"article_id": f"ERROR_{os.path.basename(file_path)}", "error": error_msg})

        return f"批量处理成功：共处理 {total_files} 个文件，拆分并分析 {article_count} 条条文。"

    def get_batch_articles(self):
        """返回本次批量处理的条文结果"""
        return self.batch_articles

    def update_article_classification(self, article_id: str, classification_key: str):
        """更新批量条文中的单个条文分类"""
        for article in self.batch_articles:
            if article.get('article_id') == article_id:
                article['classification_key'] = classification_key
                break