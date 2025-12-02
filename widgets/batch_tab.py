import os
import json
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QMessageBox, QFileDialog, QTextBrowser,
    QGridLayout, QSizePolicy, QDialog, QVBoxLayout,
    QHBoxLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QCoreApplication, QIODevice
from PySide6.QtGui import QTextOption, QColor, QPalette  # 导入 QColor 和 QPalette

# 导入核心模块 (使用绝对导入)
from ui_utils import BaseTabWidget, WorkerThread

# 保持对同级模块的相对导入
from gemini.widgets.category_dialog import CategorySelectionDialog

# 确保导入 Service (通过 services/__init__.py 桥接导入)
from services import FileManager


class BatchTabWidget(BaseTabWidget):
    def __init__(self, qingshilu_service, parent=None):
        super().__init__("batch_tab.ui", parent)

        # 修正 1: 确保 BatchTabWidget 自身能够水平和垂直拉伸
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 🌟 新增状态变量：记录当前是否处于筛选状态 🌟
        self.is_filtered = False

        # 通过依赖注入获取 Service 实例
        self.qingshilu_service = qingshilu_service
        self.file_manager = FileManager(qingshilu_service)
        self.worker = None

        # 🌟 关键：调用主题适应逻辑 🌟
        self.apply_theme_adaptation()

        self.connect_signals()

        # 关键修正: 调用拉伸设置方法
        self._ensure_vertical_stretch()

    def apply_theme_adaptation(self):
        """
        根据系统主题，设置浅色模式下的背景色为米白色 (#FFFFF0)，
        深色模式下使用 Qt 的系统默认背景色，实现自适应。
        """
        palette = self.palette()

        # 获取系统窗口颜色作为判断依据
        window_color = palette.color(QPalette.Window)

        # 判断是否为深色模式：如果窗口颜色的亮度较低（例如，R, G, B都小于128），则视为深色模式。
        # 注意：这是一个基于颜色的启发式判断，可能不完美，但在QSS不支持媒体查询时是常用方法。
        is_dark_mode = window_color.red() < 128 and window_color.green() < 128 and window_color.blue() < 128

        if not is_dark_mode:
            # ☀️ 浅色模式：强制使用米白色 (#FFFFF0)
            custom_color = QColor("#FFFFF0")

            # 设置整个 Tab 顶层 Widget 的背景
            palette.setColor(QPalette.Window, custom_color)

            # 确保应用了背景色
            self.setAutoFillBackground(True)
            self.setPalette(palette)

            # 重新设置 QTextBrowser 的护眼色常量，确保渲染时能够使用
            self.EYE_CARE_COLOR = "#FFFFF0"
        else:
            # 🌙 深色模式：保持默认，跟随系统主题
            self.setAutoFillBackground(False)

            # 在深色模式下，我们希望条文卡片使用系统背景色
            dark_mode_bg_color = palette.color(QPalette.Window).name()
            self.EYE_CARE_COLOR = dark_mode_bg_color  # 深色模式下使用系统颜色

    def _ensure_vertical_stretch(self):
        """确保 QScrollArea (索引 1) 占据 BatchTabWidget 垂直拉伸空间。"""
        main_layout = self.layout()

        if not isinstance(main_layout, QVBoxLayout):
            return

        # 布局结构确认 (基于 batch_tab.ui):
        # 索引 0: selectBatchFileButton (Stretch=0)
        # 索引 1: batchScrollArea (Stretch=1)
        # 索引 2: batchButtonLayout (Stretch=0)
        # 索引 3: notificationLabel (Stretch=0)

        if main_layout.count() >= 4:
            # 赋予 QScrollArea (索引 1) 所有垂直拉伸空间
            main_layout.setStretch(1, 1)

            # 确保按钮和标签不拉伸，保持紧凑
            main_layout.setStretch(0, 0)
            main_layout.setStretch(2, 0)
            main_layout.setStretch(3, 0)
        else:
            print("Warning: BatchTabWidget layout count is unexpected. Vertical stretch skipped.")

    def connect_signals(self):
        self.selectBatchFileButton = self.findChild(QPushButton, "selectBatchFileButton")
        self.processBatchButton = self.findChild(QPushButton, "processBatchButton")
        self.saveBatchButton = self.findChild(QPushButton, "saveBatchButton")
        # 🌟 新增：连接筛选按钮 🌟
        self.filterUnclassifiedButton = self.findChild(QPushButton, "filterUnclassifiedButton")

        self.batchContents = self.findChild(QWidget, "batchContents")

        self.notificationLabel = self.findChild(QLabel, "notificationLabel")
        if self.notificationLabel:
            self.notificationLabel.hide()

        if self.selectBatchFileButton:
            self.selectBatchFileButton.clicked.connect(self._handle_select_batch_files_controller)
        if self.processBatchButton:
            self.processBatchButton.clicked.connect(self._start_process_batch_worker)
        if self.saveBatchButton:
            self.saveBatchButton.clicked.connect(self._handle_save_batch_results)
        # 🌟 连接筛选按钮的信号 🌟
        if self.filterUnclassifiedButton:
            self.filterUnclassifiedButton.clicked.connect(self._toggle_filter_unclassified)

    def _toggle_filter_unclassified(self):
        """
        切换筛选状态：显示所有条文 或 只显示未分类条文。
        """
        if self.is_filtered:
            # 切换回显示全部
            self.is_filtered = False
            self.filterUnclassifiedButton.setText("筛选未分类")
            self.filterUnclassifiedButton.setStyleSheet("background-color: #3f689f; color: white;")
            results_to_render = self.file_manager.get_batch_articles()
            self.show_notification(f"已显示全部 {len(results_to_render)} 条条文。")
        else:
            # 切换到筛选模式
            self.is_filtered = True
            self.filterUnclassifiedButton.setText("显示全部")
            self.filterUnclassifiedButton.setStyleSheet("background-color: #ffc107; color: black;")  # 醒目颜色

            all_articles = self.file_manager.get_batch_articles()
            # 筛选出分类键为 None 或空字符串的条文
            results_to_render = [
                a for a in all_articles
                if a.get('classification_key') is None or a.get('classification_key') == ''
            ]
            self.show_notification(f"已筛选出 {len(results_to_render)} 条未分类条文。")

        self._render_batch_results(results_to_render)

    def _handle_select_batch_files_controller(self):
        """处理选择批量文件按钮的点击事件 (Controller 职责)"""
        files = self.file_manager.select_batch_files(self)

        if files:
            # 🌟 重置筛选状态 🌟
            self.is_filtered = False
            self.filterUnclassifiedButton.setText("筛选未分类")
            self.filterUnclassifiedButton.setStyleSheet("background-color: #3f689f; color: white;")

            batch_list_widget = self.findChild(QWidget, "batchContents")
            batch_list_layout = batch_list_widget.layout()

            if batch_list_layout:
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
        # 🌟 禁用筛选按钮 🌟
        self.filterUnclassifiedButton.setEnabled(False)

        self.worker = WorkerThread(self.file_manager.process_files)

        self.worker.result_signal.connect(self._on_batch_success)
        self.worker.error_signal.connect(self._on_batch_error)

        self.worker.start()

    def _on_batch_success(self, message):
        """批量处理完成后在主线程中执行，并显示结果概览"""
        self.processBatchButton.setEnabled(True)
        self.processBatchButton.setText("批量分析")
        # 🌟 启用筛选按钮 🌟
        self.filterUnclassifiedButton.setEnabled(True)

        # 始终使用完整的文章列表进行渲染，让用户决定是否筛选
        results = self.file_manager.get_batch_articles()

        # 批量处理成功后，重置筛选状态，显示全部
        self.is_filtered = False
        self.filterUnclassifiedButton.setText("筛选未分类")
        self.filterUnclassifiedButton.setStyleSheet("background-color: #3f689f; color: white;")

        self._render_batch_results(results)

        QMessageBox.information(self, "批量完成", message)

    def _on_batch_error(self, error_message):
        """批量处理失败后在主线程中执行"""
        self.processBatchButton.setEnabled(True)
        self.processBatchButton.setText("批量分析")
        # 🌟 启用筛选按钮 🌟
        self.filterUnclassifiedButton.setEnabled(True)
        QMessageBox.critical(self, "错误", f"批量处理过程中发生错误：\n{error_message}")

    def show_notification(self, message: str, is_error: bool = False):
        """显示临时的底部通知，3秒后自动隐藏"""
        if not self.notificationLabel:
            return

        style = "padding: 5px; border-radius: 3px; font-weight: bold;"

        if is_error:
            style += "background-color: #f8d7da; color: #721c24;"
        else:
            style += "background-color: #d4edda; color: #155724;"

        self.notificationLabel.setText(message)
        self.notificationLabel.setStyleSheet(style)
        self.notificationLabel.show()

        QTimer.singleShot(3000, self.notificationLabel.hide)

    def _render_batch_results(self, results):
        """将批量处理的条文结果渲染到 UI 中"""
        if not self.batchContents: return

        layout = self.batchContents.layout()
        if not layout:
            layout = QVBoxLayout(self.batchContents)
            self.batchContents.setLayout(layout)

        # 清空旧内容
        while layout.count():
            child = layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        # 🌟 使用在 apply_theme_adaptation 中设置的自适应颜色 🌟
        # 浅色模式下是 #FFFFF0，深色模式下是系统默认深色
        ARTICLE_CARD_BG = getattr(self, 'EYE_CARE_COLOR', "#FFFFF0")  # 获取自适应颜色，默认仍为米白色

        # 渲染新结果
        for result in results:
            if 'error' in result:
                # 渲染错误信息
                article_id = result.get('article_id', '未知错误')
                label = QLabel(f"错误: {article_id}\n信息: {result['error']}")
                label.setStyleSheet(
                    "color: red; font-weight: bold; padding: 5px; border: 1px solid red; background-color: #FFE0E0;")
                label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
                layout.addWidget(label)
                continue

            # 渲染条文分析结果
            article_id = result['article_id']
            category_key = result.get('classification_key')

            article_group = QWidget()
            sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            article_group.setSizePolicy(sizePolicy)

            group_layout = QGridLayout(article_group)

            # 🌟 重点修改 2: 设置 article_group 的背景为自适应颜色 🌟
            article_group.setStyleSheet(
                f"""
                QWidget {{
                    background-color: {ARTICLE_CARD_BG}; 
                    border: 1px solid #ddd; 
                    margin: 5px; 
                    padding: 5px;
                }}
                """
            )
            group_layout.setColumnStretch(0, 1)

            # 1. ID 和原文
            id_label = QLabel(f"<b>ID: {article_id}</b>")
            text_browser = QTextBrowser()
            text_browser.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            original_text = result.get('originalText', '原文内容缺失')
            text_browser.setText(original_text)
            text_browser.setMinimumHeight(150)
            text_browser.setFrameShape(QTextBrowser.NoFrame)

            # 🌟 重点修改 3: 确保 QTextBrowser 背景与 article_group 背景一致，并设置字体 🌟
            # 浅色模式下字体为黑色，深色模式下字体应为白色
            text_color = "black" if ARTICLE_CARD_BG == "#FFFFF0" else "white"

            text_browser.setStyleSheet(
                f"""
                QTextBrowser {{
                    background-color: {ARTICLE_CARD_BG}; /* 自适应背景色 */
                    color: {text_color}; /* 自适应字体颜色 */
                    font-size: 20pt; 
                    line-height: 1.5;
                }}
                """
            )

            # 2. 推荐分类
            recommendations = result['analysis'].get('recommendations', [])
            rec_container = QWidget()
            rec_layout = QHBoxLayout(rec_container)
            rec_layout.setContentsMargins(0, 0, 0, 0)
            rec_layout.setSpacing(5)

            # 🌟 确保推荐容器背景与条文卡片背景一致 🌟
            rec_container.setStyleSheet(f"background-color: {ARTICLE_CARD_BG};")

            if recommendations:
                for i, rec in enumerate(recommendations[:3]):
                    recommendation_key = rec['category']
                    display_text = f"推荐{i + 1}: {recommendation_key}"
                    rec_button = QPushButton(display_text)
                    rec_button.article_id = article_id
                    rec_button.recommendation_key = recommendation_key
                    # 按钮样式保持不变，但可以考虑在深色模式下调整颜色以增加对比度
                    rec_button.setStyleSheet(
                        "QPushButton { color: #1a3b2e; background-color: #e0f7e0; border: 1px solid #a8dfa8; padding: 3px 6px; } QPushButton:hover { background-color: #c0f0c0; }")
                    rec_button.setToolTip(f"点击即可采用推荐{i + 1}：{recommendation_key}并保存")
                    rec_button.clicked.connect(self._handle_accept_recommendation)
                    rec_layout.addWidget(rec_button)

                rec_layout.addStretch()
                rec_widget = rec_container
            else:
                rec_label = QLabel("推荐: 无")
                rec_label.setMinimumWidth(150)
                # 确保标签颜色在深色模式下可见
                rec_label.setStyleSheet(f"color: {text_color};")
                rec_widget = rec_label

            # 3. 当前分类状态
            current_cat_text = category_key if category_key else "未分类"
            current_cat_label = QLabel(f"状态: <b>{current_cat_text}</b>")

            if category_key:
                current_cat_label.setStyleSheet("color: #00A896; font-weight: bold;")
            else:
                current_cat_label.setStyleSheet("color: #FF6F00; font-weight: bold;")

            # 4. 分类按钮
            classify_btn = QPushButton("手动分类/修改")
            classify_btn.article_id = article_id
            classify_btn.clicked.connect(self._handle_classify_article)

            # 布局控件
            group_layout.addWidget(id_label, 0, 0, 1, 3)
            group_layout.addWidget(text_browser, 1, 0, 1, 3)
            group_layout.addWidget(rec_widget, 2, 0)
            group_layout.addWidget(current_cat_label, 2, 1)
            group_layout.addWidget(classify_btn, 2, 2)

            layout.addWidget(article_group)

        # 添加伸展空间，确保内容顶部对齐
        layout.addStretch()

        # 🌟 筛选状态提示 🌟
        if self.is_filtered:
            self.show_notification(f"当前显示 {len(results)} 条未分类条文。", is_error=False)

    def _convert_display_key_to_save_key(self, display_key: str) -> str | None:
        """
        将 L1Name-L2Name-L3Name 的显示格式
        转换为 Service 要求的 L1Key/L2Name/L3Name (例如: 0/赈灾与民生保障/赈灾)
        """
        parts = display_key.split('-')
        if len(parts) != 3:
            return None

        level1_name = parts[0]

        if level1_name == "事务类":
            l1_key = "0"
        elif level1_name == "问题类":
            l1_key = "1"
        else:
            return None

        # 构造 Service 要求的保存格式： L1_KEY/L2_NAME/L3_NAME
        return f"{l1_key}/{parts[1]}/{parts[2]}"

    def _handle_accept_recommendation(self):
        """处理点击推荐分类按钮的事件：直接采用推荐分类并保存"""
        sender_button = self.sender()
        if not hasattr(sender_button, 'article_id') or not hasattr(sender_button, 'recommendation_key'):
            QMessageBox.critical(self, "错误", "无法识别按钮关联的条文ID或推荐分类。")
            return

        article_id = sender_button.article_id
        display_key = sender_button.recommendation_key

        classification_key = self._convert_display_key_to_save_key(display_key)

        if not classification_key:
            QMessageBox.critical(self, "错误", f"无法解析推荐分类键 '{display_key}' 为保存格式，请手动分类。")
            return

        current_article = next((a for a in self.file_manager.get_batch_articles() if a['article_id'] == article_id),
                               None)
        if not current_article:
            QMessageBox.critical(self, "错误", f"未找到条文ID: {article_id}")
            return

        self._perform_save_classification(article_id, classification_key, current_article)

    def _perform_save_classification(self, article_id, classification_key, current_article):
        """将分类保存到 Service，并更新 UI"""
        try:
            self.file_manager.update_article_classification(article_id, classification_key)

            self.qingshilu_service.save_classification_result(
                current_article['originalText'],
                current_article['analysis'].get('translation', 'N/A'),
                classification_key,
                article_id=article_id
            )

            self.show_notification(f"分类成功：条文 {article_id} 已保存到: {classification_key}")

            # 🌟 修正：根据当前的筛选状态重新渲染 🌟
            if self.is_filtered:
                all_articles = self.file_manager.get_batch_articles()
                results_to_render = [
                    a for a in all_articles
                    if a.get('classification_key') is None or a.get('classification_key') == ''
                ]
            else:
                results_to_render = self.file_manager.get_batch_articles()

            self._render_batch_results(results_to_render)

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"分类保存失败: {e}")

    def _handle_classify_article(self):
        """处理批量结果中的单条条文分类（手动选择）"""
        sender_button = self.sender()
        if not hasattr(sender_button, 'article_id'):
            QMessageBox.critical(self, "错误", "无法识别按钮关联的条文ID。")
            return

        article_id = sender_button.article_id

        current_article = next((a for a in self.file_manager.get_batch_articles() if a['article_id'] == article_id),
                               None)
        if not current_article:
            QMessageBox.critical(self, "错误", f"未找到条文ID: {article_id}")
            return

        category_dialog = CategorySelectionDialog(self.qingshilu_service.get_category_structure(), self)
        if category_dialog.exec() == QDialog.Accepted:
            classification_key = category_dialog.get_selected_key()

            self._perform_save_classification(article_id, classification_key, current_article)

    def _handle_save_batch_results(self):
        """处理批量保存结果的逻辑"""
        results = self.file_manager.get_batch_articles()

        if not results:
            QMessageBox.warning(self, "警告", "没有批量分析结果可供保存。")
            return

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
