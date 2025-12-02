# main.py
# 主程序入口：负责 UI 加载、模块组装、信号连接 (View/Controller/Coordinator)

import sys
import os
import traceback

# main.py (顶部导入 QWidget 的地方)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QWidget, QLabel, QTextEdit,
    QPushButton, QMenuBar, QStatusBar, QTabWidget, QDialog, QComboBox,
    QTextBrowser, QGridLayout, QScrollArea, QVBoxLayout, QFileDialog, QSizePolicy # <--- 新增 QSizePolicy
)
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtCore import QFile, QIODevice, Qt, QThread, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QCoreApplication

# 导入核心服务类
from services import QingShiluService, FileManager


# =======================================================
# 异步处理机制 (Worker Thread)
# =======================================================

class WorkerThread(QThread):
    """
    通用工作线程：在后台执行 Service 层的同步阻塞方法。
    """
    result_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.result_signal.emit(result)
        except Exception:
            error_msg = traceback.format_exc()
            self.error_signal.emit(error_msg)


# =======================================================
# 辅助函数和 Tab 基类
# =======================================================

def load_ui_file(loader, ui_file_name, parent_widget):
    """
    加载指定的 .ui 文件并返回打开的文件对象。
    【注意】路径已更新为查找 ./ui/ 目录
    """
    # 查找脚本所在目录的 'ui' 子目录
    ui_dir = os.path.join(os.path.dirname(__file__), "ui")
    ui_path = os.path.join(ui_dir, ui_file_name)
    ui_file = QFile(ui_path)

    if not ui_file.exists():
        QMessageBox.critical(parent_widget, "文件错误", f"UI文件未找到: {ui_path}")
        return None

    if not ui_file.open(QIODevice.ReadOnly | QIODevice.Text):
        QMessageBox.critical(parent_widget, "文件错误", f"无法打开UI文件: {ui_path}")
        return None

    return ui_file


class BaseTabWidget(QWidget):
    """所有 Tab 模块的基类，包含加载自身的 UI 逻辑"""

    def __init__(self, ui_file_name, parent=None):
        super().__init__(parent)
        self.loader = QUiLoader()
        self.ui_file_name = ui_file_name
        self.load_ui()

    def load_ui(self):
        ui_file = load_ui_file(self.loader, self.ui_file_name, self)
        if ui_file is None:
            return
        self.loader.load(ui_file, self)
        ui_file.close()


# =======================================================
# 1. 单条文本处理 Tab (Controller 职责)
# =======================================================
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


# =======================================================
# 2. 批量处理 Tab (Controller 职责) - 修复冗余和逻辑错误
# =======================================================
class BatchTabWidget(BaseTabWidget):
    def __init__(self, qingshilu_service, parent=None):
        super().__init__("batch_tab.ui", parent)
        # 通过依赖注入获取 Service 实例
        self.qingshilu_service = qingshilu_service
        self.file_manager = FileManager(qingshilu_service)  # FileManager 现依赖 QingShiluService
        self.worker = None
        self.connect_signals()

    def connect_signals(self):
        self.selectBatchFileButton = self.findChild(QPushButton, "selectBatchFileButton")
        self.processBatchButton = self.findChild(QPushButton, "processBatchButton")
        self.saveBatchButton = self.findChild(QPushButton, "saveBatchButton")
        self.batchContents = self.findChild(QWidget, "batchContents")

        if self.selectBatchFileButton:
            self.selectBatchFileButton.clicked.connect(self._handle_select_batch_files_controller)
        if self.processBatchButton:
            self.processBatchButton.clicked.connect(self._start_process_batch_worker)
        if self.saveBatchButton:
            self.saveBatchButton.clicked.connect(self._handle_save_batch_results)

    def _handle_select_batch_files_controller(self):
        """处理选择批量文件按钮的点击事件 (Controller 职责)"""
        files = self.file_manager.select_batch_files(self)

        if files:
            batch_list_widget = self.findChild(QWidget, "batchContents")

            if batch_list_widget and batch_list_widget.layout():
                batch_list_layout = batch_list_widget.layout()

                # 清空旧文件列表
                while batch_list_layout.count():
                    child = batch_list_layout.takeAt(0)
                    if child and child.widget():
                        child.widget().deleteLater()

                # Controller 负责 UI 的更新
                for file in files:
                    file_label = QLabel(os.path.basename(file))
                    file_label.setToolTip(file)
                    batch_list_layout.addWidget(file_label)

                batch_list_layout.addStretch()
                QMessageBox.information(self, "提示", f"已选择了 {len(files)} 个文件。")

    def _start_process_batch_worker(self):
        """启动异步批量处理线程"""
        if not self.file_manager.get_selected_files():
            QMessageBox.warning(self, "警告", "请先选择需要处理的文件。")
            return

        self.processBatchButton.setEnabled(False)
        self.processBatchButton.setText("批量处理中...")

        self.worker = WorkerThread(self.file_manager.process_files)

        self.worker.result_signal.connect(self._on_batch_success)
        self.worker.error_signal.connect(self._on_batch_error)

        self.worker.start()

    def _on_batch_success(self, message):
        """批量处理完成后在主线程中执行，并显示结果概览"""
        self.processBatchButton.setEnabled(True)
        self.processBatchButton.setText("批量分析")

        results = self.file_manager.get_batch_articles()

        self._render_batch_results(results)

        QMessageBox.information(self, "批量完成", message)

    def _on_batch_error(self, error_message):
        """批量处理失败后在主线程中执行"""
        self.processBatchButton.setEnabled(True)
        self.processBatchButton.setText("批量分析")
        QMessageBox.critical(self, "错误", f"批量处理过程中发生错误：\n{error_message}")

    def _render_batch_results(self, results):
        """将批量处理的条文结果渲染到 UI 中，并确保水平自适应和全量条文显示"""
        # 假设 QSizePolicy 已在 main.py 顶部导入
        from PySide6.QtWidgets import QSizePolicy

        if not self.batchContents: return

        # 确保 batchContents 有一个垂直布局
        layout = self.batchContents.layout()
        if not layout:
            layout = QVBoxLayout(self.batchContents)
            self.batchContents.setLayout(layout)

        # 清空旧内容
        while layout.count():
            child = layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        # 渲染新结果
        for result in results:
            if 'error' in result:
                # 渲染错误信息
                article_id = result.get('article_id', '未知错误')
                label = QLabel(f"错误: {article_id}\n信息: {result['error']}")
                label.setStyleSheet("color: red; font-weight: bold; padding: 5px; border: 1px solid red;")

                # 确保错误标签也占据水平空间
                label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
                layout.addWidget(label)
                continue

            # 渲染条文分析结果
            article_id = result['article_id']
            category_key = result.get('classification_key')

            # 创建一个用于展示条文的容器
            article_group = QWidget()

            # 【关键修正 1：设置水平拉伸策略】
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            article_group.setSizePolicy(sizePolicy)

            # 使用 QGridLayout 以便更好地控制布局
            group_layout = QGridLayout(article_group)
            article_group.setStyleSheet("border: 1px solid #ddd; margin: 5px; padding: 5px;")

            # 确保 QGridLayout 的列拉伸
            group_layout.setColumnStretch(0, 1)  # 让第一列 (ID/推荐/文本) 占据大部分空间

            # 1. ID 和原文摘要
            id_label = QLabel(f"<b>ID: {article_id}</b>")
            text_browser = QTextBrowser()  # 使用 QTextBrowser 允许更好的文本渲染和滚动

            # 【关键修正 2：全量显示和高度调整】
            original_text = result.get('originalText', '原文内容缺失')
            text_browser.setText(original_text)  # 显示全量条文

            # 移除 setMaximumHeight(200)。使用一个更大的默认高度，并让 QTextBrowser 自动提供滚动条
            text_browser.setMinimumHeight(150)  # 至少设置为 150 像素，确保有足够的阅读空间

            # 2. 推荐分类
            recommendations = result['analysis'].get('recommendations', [])
            recommendation = recommendations[0]['category'] if recommendations else '无推荐'
            rec_label = QLabel(f"推荐: {recommendation}")
            rec_label.setMinimumWidth(150)  # 确保推荐标签有最小宽度

            # 3. 当前分类状态
            current_cat_text = category_key if category_key else "未分类"
            current_cat_label = QLabel(f"状态: <b>{current_cat_text}</b>")
            current_cat_label.setStyleSheet("color: blue;" if category_key else "color: orange;")

            # 4. 分类按钮
            classify_btn = QPushButton("分类/修改")
            classify_btn.article_id = article_id
            classify_btn.clicked.connect(self._handle_classify_article)

            # 布局控件
            # ID 标签
            group_layout.addWidget(id_label, 0, 0, 1, 3)

            # 文本摘要，跨越所有 3 列
            group_layout.addWidget(text_browser, 1, 0, 1, 3)

            # 推荐、状态和按钮在第三行
            group_layout.addWidget(rec_label, 2, 0)
            group_layout.addWidget(current_cat_label, 2, 1)
            group_layout.addWidget(classify_btn, 2, 2)

            layout.addWidget(article_group)

        # 添加伸展空间，确保内容顶部对齐
        layout.addStretch()

    # === 处理单条条文分类 (修复了 AttributeError: '_handle_classify_article' 的问题) ===
    def _handle_classify_article(self):
        """处理批量结果中的单条条文分类"""
        sender_button = self.sender()
        if not hasattr(sender_button, 'article_id'):
            QMessageBox.critical(self, "错误", "无法识别按钮关联的条文ID。")
            return

        article_id = sender_button.article_id

        # 查找当前条文数据
        current_article = next((a for a in self.file_manager.get_batch_articles() if a['article_id'] == article_id),
                               None)
        if not current_article:
            QMessageBox.critical(self, "错误", f"未找到条文ID: {article_id}")
            return

        # 弹出分类选择对话框
        category_dialog = CategorySelectionDialog(self.qingshilu_service.get_category_structure(), self)
        if category_dialog.exec() == QDialog.Accepted:
            classification_key = category_dialog.get_selected_key()

            # 1. 更新内存中的分类状态
            self.file_manager.update_article_classification(article_id, classification_key)

            # 2. 保存到持久化存储
            try:
                # 使用 self.qingshilu_service
                self.qingshilu_service.save_classification_result(
                    current_article['originalText'],
                    current_article['analysis'].get('translation', 'N/A'),
                    classification_key,
                    article_id=article_id
                )
                QMessageBox.information(self, "分类成功", f"条文 {article_id} 已保存到: {classification_key}")

                # 3. 重新渲染结果列表以显示更新后的状态
                self._render_batch_results(self.file_manager.get_batch_articles())

            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"分类保存失败: {e}")

    # === 批量保存结果 ===
        # main.py (BatchTabWidget 类的 _handle_save_batch_results 方法)

    def _handle_save_batch_results(self):
        """处理批量保存结果的逻辑"""
        # 批量保存应该导出所有条文的当前状态（包括分类结果）
        results = self.file_manager.get_batch_articles()

        if not results:
            QMessageBox.warning(self, "警告", "没有批量分析结果可供保存。")
            return

        # 确保 QFileDialog 在 main.py 顶部已导入
        # 需要 import json 模块，如果它不在顶部，则在方法内导入
        import json
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存批量结果", "batch_analysis_results.json", "JSON 文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "保存成功", f"批量结果已成功保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"无法保存文件: {e}")
# =======================================================
# 3. 关键词管理 Tab (实现关键词管理逻辑)
# =======================================================

# main.py (修正后的 KeywordTabWidget 类)

# =======================================================
# 3. 关键词管理 Tab (实现关键词管理逻辑)
# =======================================================

class KeywordTabWidget(BaseTabWidget):
    def __init__(self, qingshilu_service, parent=None):
        super().__init__("keyword_tab.ui", parent)
        self.service = qingshilu_service
        self.connect_signals()

        # 修复后的代码：确保方法存在于类中
        self._load_category_options()

    def connect_signals(self):
        # 确保这些控件已被加载 (在前一轮修复 UI 文件后应已存在)
        self.keywordCategorySelect = self.findChild(QComboBox, "keywordCategorySelect")
        self.keywordInput = self.findChild(QTextEdit, "keywordInput")
        self.currentKeywordsText = self.findChild(QTextEdit, "currentKeywordsText")
        self.saveKeywordsButton = self.findChild(QPushButton, "saveKeywordsButton")

        if self.keywordCategorySelect:
            self.keywordCategorySelect.currentIndexChanged.connect(self._load_keywords_for_category)
        if self.saveKeywordsButton:
            self.saveKeywordsButton.clicked.connect(self._save_keywords_controller)

    # 【关键缺失方法】
    def _load_category_options(self):
        """加载下拉菜单选项"""
        # 健壮性检查 (保留，确保即使UI文件出错也不会崩溃)
        if self.keywordCategorySelect is None:
            QMessageBox.critical(self, "UI错误",
                                 "无法找到关键词分类选择框(keywordCategorySelect)。请检查 keyword_tab.ui 文件中的 objectName。")
            return

        self.category_map = self.service.get_all_categories_map()
        self.keywordCategorySelect.clear()

        for category_key in self.category_map.keys():
            self.keywordCategorySelect.addItem(category_key.replace('-', ' → '), category_key)

        self._load_keywords_for_category(0)  # 默认加载第一个

    # 【关键辅助方法】
    def _load_keywords_for_category(self, index):
        """根据选择的分类加载关键词到输入框和展示区域"""
        if index < 0: return

        # 健壮性检查
        if self.keywordCategorySelect is None: return

        category_key = self.keywordCategorySelect.itemData(index)
        if not category_key: return

        keywords = self.service.get_keywords_for_category(category_key)

        # 加载到输入框
        if self.keywordInput:
            self.keywordInput.setText(", ".join(keywords))

        # 加载到展示区域（模拟 JS 的标红效果）
        if self.currentKeywordsText:
            keywords_html = "".join(
                [f'<span style="color: blue; font-weight: bold; margin-right: 5px;">{kw}</span>' for kw in keywords])
            self.currentKeywordsText.setHtml(
                f'<div style="background-color: #eef; padding: 5px; border-radius: 5px;">{keywords_html}</div>')

    # 【关键辅助方法】
    def _save_keywords_controller(self):
        """保存关键词到 Service"""
        # 健壮性检查
        if self.keywordCategorySelect is None or self.keywordInput is None: return

        index = self.keywordCategorySelect.currentIndex()
        if index < 0:
            QMessageBox.warning(self, "警告", "请选择一个分类。")
            return

        category_key = self.keywordCategorySelect.itemData(index)
        keywords_text = self.keywordInput.toPlainText()

        # 清理关键词列表 (移除空格和空字符串)
        keywords = [k.strip() for k in keywords_text.split(',')]
        keywords = [k for k in keywords if k]

        try:
            self.service.save_keywords(category_key, keywords)
            QMessageBox.information(self, "保存成功", f"'{category_key}' 的关键词已更新并保存。")
            # 重新加载以显示更新后的结果
            self._load_keywords_for_category(index)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"关键词保存失败: {e}")


# =======================================================
# 4 & 5. 统计查看 Tab / 分类管理 Tab (占位模块, 保持不变)
# =======================================================
# main.py (StatsTabWidget 的增强)

# 重新定义 StatsTabWidget，使其具备 Service 依赖

class StatsTabWidget(BaseTabWidget):
    def __init__(self, qingshilu_service, parent=None):  # 接受 Service 依赖
        super().__init__("stats_tab.ui", parent)
        self.service = qingshilu_service
        self.connect_signals()
        self.load_stats_data()

    def connect_signals(self):
        self.statsTextBrowser = self.findChild(QTextBrowser, "statsTextBrowser")  # 假设 UI 中有这个控件
        self.exportCsvButton = self.findChild(QPushButton, "exportCsvButton")  # 假设 UI 中有这个按钮

        if self.exportCsvButton:
            self.exportCsvButton.clicked.connect(self._handle_export_csv)

    def load_stats_data(self):
        """从 Service 获取分类数据并渲染统计信息"""
        classified_data = self.service.model.get_all_classified_data()

        total_count = 0
        html = '<h3 style="color:#2d5a3e;">已分类条文统计</h3><hr>'

        for l1_key, l1_data in classified_data.items():
            l1_name = "事务类" if l1_key == '0' else "问题类"
            html += f"<h4>[{l1_name}] {l1_key}集 ({sum(len(l3) for l2 in l1_data.values() for l3 in l2.values())} 条)</h4>"

            for l2_key, l2_data in l1_data.items():
                l2_count = sum(len(l3) for l3 in l2_data.values())
                html += f"<ul><li><b>{l2_key} ({l2_count} 条):</b>"

                for l3_key, articles in l2_data.items():
                    article_count = len(articles)
                    total_count += article_count
                    html += f"<span style='margin-left: 20px;'>{l3_key} ({article_count} 条)</span>"

                html += "</li></ul>"

        html = f"<h2>总计已分类条文: {total_count} 条</h2>" + html

        if self.statsTextBrowser:
            self.statsTextBrowser.setHtml(html)

    def _handle_export_csv(self):
        """处理导出 CSV 按钮点击"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出分类结果", "classified_results.csv", "CSV 文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            success = self.service.model.export_classified_data_to_csv(file_path)
            if success:
                QMessageBox.information(self, "导出成功", f"所有分类结果已成功导出到: {file_path}")
            else:
                QMessageBox.critical(self, "导出失败", "导出 CSV 文件时发生错误，请检查权限或控制台输出。")


# ... (main.py 中 MainWindow._add_tab_modules 的 StatsTabWidget 实例化也需要更新)


class CategoryTabWidget(BaseTabWidget):
    def __init__(self, parent=None):
        super().__init__("category_tab.ui", parent)


# =======================================================
# 三级分类选择对话框 (用于保存分类结果)
# =======================================================
class CategorySelectionDialog(QDialog):
    def __init__(self, category_structure, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择分类路径")
        self.category_structure = category_structure
        self.selected_key = None

        self.level1_combo = QComboBox(self)
        self.level2_combo = QComboBox(self)
        self.level3_combo = QComboBox(self)
        self.ok_button = QPushButton("确定", self)
        self.cancel_button = QPushButton("取消", self)

        self._setup_ui()
        self._load_level1()
        self._connect_signals()

    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.addWidget(QLabel("一级分类 (集):"), 0, 0)
        layout.addWidget(self.level1_combo, 0, 1)
        layout.addWidget(QLabel("二级分类 (类):"), 1, 0)
        layout.addWidget(self.level2_combo, 1, 1)
        layout.addWidget(QLabel("三级分类 (项):"), 2, 0)
        layout.addWidget(self.level3_combo, 2, 1)
        layout.addWidget(self.ok_button, 3, 1)
        layout.addWidget(self.cancel_button, 3, 0)

    def _connect_signals(self):
        self.level1_combo.currentIndexChanged.connect(self._load_level2)
        self.level2_combo.currentIndexChanged.connect(self._load_level3)
        self.ok_button.clicked.connect(self._accept_selection)
        self.cancel_button.clicked.connect(self.reject)

    def _load_level1(self):
        self.level1_combo.clear()
        for key in self.category_structure.keys():
            name = "事务类" if key == '0' else "问题类"
            self.level1_combo.addItem(f"{key}集: {name}", key)
        self._load_level2(0)

    def _load_level2(self, index):
        self.level2_combo.clear()
        if index < 0: return

        l1_key = self.level1_combo.itemData(index)
        if l1_key in self.category_structure:
            for key in self.category_structure[l1_key].keys():
                self.level2_combo.addItem(key)
        self._load_level3(0)

    def _load_level3(self, index):
        self.level3_combo.clear()
        l1_key = self.level1_combo.currentData()
        l2_key = self.level2_combo.currentText()

        if l1_key and l2_key and l2_key in self.category_structure[l1_key]:
            for key in self.category_structure[l1_key][l2_key].keys():
                self.level3_combo.addItem(key)

    def _accept_selection(self):
        l1 = self.level1_combo.currentData()
        l2 = self.level2_combo.currentText()
        l3 = self.level3_combo.currentText()

        if not (l1 and l2 and l3):
            QMessageBox.warning(self, "警告", "请选择完整的分类路径。")
            return

        self.selected_key = f"{l1}/{l2}/{l3}"
        self.accept()

    def get_selected_key(self):
        return self.selected_key


# =======================================================
# 主窗口 (Coordinator)
# =======================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loader = QUiLoader()
        self.ui_loaded = False

        # --- 实例化 Service 层，供所有 Tab 共享 ---
        self.qingshilu_service = QingShiluService()

        # --- 1. 加载主窗口外壳 ---
        ui_file = load_ui_file(self.loader, "main_window.ui", self)
        if ui_file is None: return

        temp_window = self.loader.load(ui_file)
        ui_file.close()

        if temp_window is None:
            QMessageBox.critical(self, "加载错误", "无法从 main_window.ui 加载内容。")
            return

        # 转移主结构、Actions等 (省略细节，假设与上一步一致)
        # ... (转移代码) ...
        centralwidget = temp_window.centralWidget()
        if centralwidget:
            centralwidget.setParent(self)
            self.setCentralWidget(centralwidget)
        if temp_window.menuBar():
            temp_window.menuBar().setParent(self)
        if temp_window.statusBar():
            temp_window.statusBar().setParent(self)
            self.setStatusBar(temp_window.statusBar())
        self.setWindowTitle(temp_window.windowTitle())
        self.resize(temp_window.size())
        self.actions = {}
        for action_name in ["actionGoToSingle", "actionGoToBatch", "actionGoToKeyword", "actionGoToStatistics",
                            "actionGoToCategory"]:
            action = temp_window.findChild(QAction, action_name)
            if action:
                action.setParent(self)
                self.actions[action_name] = action
        temp_window.deleteLater()
        self.ui_loaded = True

        # --- 2. 组装 Tab 模块 (Composition) ---
        self.mainTabWidget = self.findChild(QTabWidget, "mainTabWidget")
        if self.mainTabWidget:
            self._add_tab_modules()
            self._connect_menu_actions()

        # main.py (MainWindow._add_tab_modules 的修正)

    def _add_tab_modules(self):
        """实例化并添加所有 Tab 模块到 QTabWidget"""
        self.mainTabWidget.clear()

        # 【关键】将 QingShiluService 实例注入到各个 Tab 中
        self.single_tab = SingleTabWidget(self.qingshilu_service, self.mainTabWidget)
        self.mainTabWidget.addTab(self.single_tab, "1. 单条文本处理")

        # 修复：完整实例化 BatchTabWidget
        self.batch_tab = BatchTabWidget(self.qingshilu_service, self.mainTabWidget)
        self.mainTabWidget.addTab(self.batch_tab, "2. 批量处理")

        self.keyword_tab = KeywordTabWidget(self.qingshilu_service, self.mainTabWidget)
        self.mainTabWidget.addTab(self.keyword_tab, "3. 关键词管理")

        self.stats_tab = StatsTabWidget(self.qingshilu_service, self.mainTabWidget)
        self.mainTabWidget.addTab(self.stats_tab, "4. 统计查看")

        self.category_tab = CategoryTabWidget(self.mainTabWidget)
        self.mainTabWidget.addTab(self.category_tab, "5. 分类管理")

    def _connect_menu_actions(self):
        """连接菜单栏 Actions 到 Tab 切换"""
        menu_to_index = {
            "actionGoToSingle": 0, "actionGoToBatch": 1,
            "actionGoToKeyword": 2, "actionGoToStatistics": 3,
            "actionGoToCategory": 4,
        }
        for action_name, index in menu_to_index.items():
            action = self.actions.get(action_name)
            if action:
                action.triggered.connect(lambda checked, i=index: self.set_current_tab(i))

    def set_current_tab(self, index):
        """根据索引切换主 Tab 页 (MainWindow 的职责)"""
        if self.mainTabWidget:
            self.mainTabWidget.setCurrentIndex(index)


# --- 应用程序入口点 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    if hasattr(window, 'ui_loaded') and window.ui_loaded:
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(1)