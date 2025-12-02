# /Users/luckpuppy/Desktop/UItools/gemini/widgets/single_tab.py

from PySide6.QtWidgets import (
    QTextEdit, QPushButton, QLabel, QTextBrowser, QDialog, QMessageBox
)
# 使用绝对导入 ui_utils (因为 main.py 已经将 gemini 目录添加到了 sys.path)
from ui_utils import BaseTabWidget, WorkerThread

# 保持对同级模块的相对导入
from gemini.widgets.category_dialog import CategorySelectionDialog
# ... (SingleTabWidget 类的其余代码保持不变) ...


class SingleTabWidget(BaseTabWidget):
    def __init__(self, qingshilu_service, parent=None):
        super().__init__("single_tab.ui", parent)
        # 通过依赖注入获取 Service 实例
        self.analysis_service = qingshilu_service
        self.worker = None
        self.current_analysis_results = None  # 存储Service返回的全部结果
        self.connect_signals()
        self._update_char_count_controller()

    def connect_signals(self):
        # 假设 single_tab.ui 中有这些控件
        self.originalTextEdit = self.findChild(QTextEdit, "originalTextEdit")
        self.translationTextEdit = self.findChild(QTextEdit, "translationTextEdit")
        self.charCountLabel = self.findChild(QLabel, "charCountLabel")
        self.analyzeButton = self.findChild(QPushButton, "analyzeButton")
        self.copyButton = self.findChild(QPushButton, "copyButton")
        self.saveClassificationButton = self.findChild(QPushButton, "saveClassificationButton")

        # 假设用于展示分析结果的控件
        self.coreInfoLabel = self.findChild(QLabel, "coreInfoLabel")
        self.recommendationsText = self.findChild(QTextBrowser, "recommendationsText")
        self.similarTextsText = self.findChild(QTextBrowser, "similarTextsText")
        self.keywordsText = self.findChild(QTextEdit, "keywordsText")

        # 连接逻辑
        if self.originalTextEdit:
            self.originalTextEdit.textChanged.connect(self._update_char_count_controller)
        if self.analyzeButton:
            self.analyzeButton.clicked.connect(self._start_smart_analyze_worker)
        if self.saveClassificationButton:
            self.saveClassificationButton.clicked.connect(self._save_classification_controller)

    # --- Controller 方法 ---

    def _update_char_count_controller(self):
        if self.originalTextEdit and self.charCountLabel:
            count = len(self.originalTextEdit.toPlainText())
            self.charCountLabel.setText(f"字符数: {count}")

    def _start_smart_analyze_worker(self):
        """启动异步分析线程"""
        text = self.originalTextEdit.toPlainText()

        if not text:
            QMessageBox.warning(self, "输入为空", "请输入原文内容进行分析。")
            return

        # UI 状态：禁用按钮，显示加载信息
        self.analyzeButton.setEnabled(False)
        self.analyzeButton.setText("正在分析...")
        self.translationTextEdit.setText("正在调用 Service 层进行智能分析，请稍候...")
        self.coreInfoLabel.setText("核心信息: 正在提取...")
        self.recommendationsText.setText("推荐分类: 正在计算...")
        self.similarTextsText.setText("相似文本: 正在检索...")
        self.keywordsText.setText("")

        # 创建 WorkerThread：调用 Service.run_full_analysis 方法
        self.worker = WorkerThread(self.analysis_service.run_full_analysis, text)

        # 连接信号
        self.worker.result_signal.connect(self._on_analysis_success)
        self.worker.error_signal.connect(self._on_analysis_error)
        self.worker.start()

    def _on_analysis_success(self, results):
        """在主线程中处理 Service 返回的成功结果，并更新所有 UI 区域"""
        # 恢复 UI 状态
        self.analyzeButton.setEnabled(True)
        self.analyzeButton.setText("智能分析")

        self.current_analysis_results = results

        # 1. 翻译和核心信息
        self.translationTextEdit.setText(results['translation'])

        info = results['core_info']
        self.coreInfoLabel.setText(
            f"主体: {info.get('subject', 'N/A')} | 动作: {info.get('action', 'N/A')} | 性质: {info.get('nature', 'N/A')}"
        )

        # 2. 关键词标红
        keywords_html = "".join(
            [f'<span style="color: red; font-weight: bold;">{kw}</span> ' for kw in results['keywords']])
        self.keywordsText.setHtml(
            f'<div style="background-color: #f0f0f0; padding: 5px; border-radius: 5px;">{keywords_html}</div>')

        # 3. 分类推荐 (模拟卡片 UI)
        rec_html = self._render_recommendations_html(results['recommendations'])
        self.recommendationsText.setHtml(rec_html)

        # 4. 相似文本 (模拟卡片 UI)
        similar_html = self._render_similar_texts_html(results['similar_texts'])
        self.similarTextsText.setHtml(similar_html)

        QMessageBox.information(self, "分析完成", "智能分析和推荐已完成。")

    def _on_analysis_error(self, error_message):
        """在主线程中处理 Service 返回的错误信息"""
        self.analyzeButton.setEnabled(True)
        self.analyzeButton.setText("智能分析")
        self.translationTextEdit.setText(f"分析失败。详情请看控制台。\n{error_message}")
        QMessageBox.critical(self, "错误", "分析过程中发生致命错误。")
        self.current_analysis_results = None

    def _save_classification_controller(self):
        """保存分类结果（JS: saveClassification）"""
        if not self.current_analysis_results:
            QMessageBox.warning(self, "警告", "请先运行分析并选择分类。")
            return

        original_text = self.originalTextEdit.toPlainText()
        translation = self.translationTextEdit.toPlainText()

        category_dialog = CategorySelectionDialog(self.analysis_service.get_category_structure(), self)
        if category_dialog.exec() == QDialog.Accepted:
            classification_key = category_dialog.get_selected_key()  # 格式: '0/赈灾与民生保障/赈灾'

            try:
                # 【新增】调用 save_classification_result 时，article_id 传 None
                self.analysis_service.save_classification_result(
                    original_text, translation, classification_key, article_id=None
                )
                QMessageBox.information(self, "保存成功", f"文本已成功保存到: {classification_key}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存失败: {e}")

    # --- UI 渲染辅助方法 ---
    def _render_recommendations_html(self, recommendations):
        html = '<div style="font-family: Arial, sans-serif; padding: 5px;">'
        if not recommendations:
            return "暂无强相关推荐。"

        for rec in recommendations:
            html += f"""
            <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 8px; border-radius: 5px; background-color: #f9f9f9;">
                <p style="margin: 0; font-weight: bold; color: #1a3b2e;">{rec['level1']} → {rec['level2']} → {rec['level3']}</p>
                <p style="margin: 3px 0; font-size: 10pt; color: #555;">匹配度: {rec['score']} - {rec['reason']}</p>
                <p style="margin: 0; font-size: 9pt; color: #777;">关键词: {', '.join(rec['matchedKeywords'])}</p>
            </div>
            """
        html += '</div>'
        return html

    def _render_similar_texts_html(self, similar_texts):
        html = '<div style="font-family: Arial, sans-serif; padding: 5px;">'
        if not similar_texts:
            return "暂无相似历史文本。"

        for text in similar_texts:
            html += f"""
            <div style="border: 1px solid #eee; padding: 8px; margin-bottom: 5px; border-radius: 4px; background-color: #fcfcfc;">
                <p style="margin: 0; font-size: 10pt; color: #2d5a3e;">分类: {text['categoryPath']} (相似度: {text['similarity']})</p>
                <p style="margin: 3px 0; font-size: 9pt; color: #777;">原文: {text['originalText'][:50]}...</p>
                <p style="margin: 0; font-size: 8pt; color: #aaa;">关键词: {', '.join(text['commonKeywords'])}</p>
            </div>
            """
        html += '</div>'
        return html