# widgets/keyword_tab.py

from PySide6.QtWidgets import (
    QComboBox, QTextEdit, QPushButton, QMessageBox
)

from ui_utils import BaseTabWidget, WorkerThread


class KeywordTabWidget(BaseTabWidget):
    def __init__(self, qingshilu_service, parent=None):
        super().__init__("keyword_tab.ui", parent)
        self.service = qingshilu_service
        self.connect_signals()

        # 确保方法存在于类中
        self._load_category_options()

    def connect_signals(self):
        # 确保这些控件已被加载
        self.keywordCategorySelect = self.findChild(QComboBox, "keywordCategorySelect")
        self.keywordInput = self.findChild(QTextEdit, "keywordInput")
        self.currentKeywordsText = self.findChild(QTextEdit, "currentKeywordsText")
        self.saveKeywordsButton = self.findChild(QPushButton, "saveKeywordsButton")

        if self.keywordCategorySelect:
            self.keywordCategorySelect.currentIndexChanged.connect(self._load_keywords_for_category)
        if self.saveKeywordsButton:
            self.saveKeywordsButton.clicked.connect(self._save_keywords_controller)

    def _load_category_options(self):
        """加载下拉菜单选项"""
        # 健壮性检查
        if self.keywordCategorySelect is None:
            QMessageBox.critical(self, "UI错误",
                                 "无法找到关键词分类选择框(keywordCategorySelect)。请检查 keyword_tab.ui 文件中的 objectName。")
            return

        # 假设 service.get_all_categories_map() 返回包含所有分类路径的字典
        self.category_map = self.service.get_all_categories_map()
        self.keywordCategorySelect.clear()

        for category_key in self.category_map.keys():
            # 这里的替换是为了在 UI 中显示更友好的路径名
            self.keywordCategorySelect.addItem(category_key.replace('-', ' → '), category_key)

        # 默认加载第一个分类的关键词
        self._load_keywords_for_category(0)

    def _load_keywords_for_category(self, index):
        """根据选择的分类加载关键词到输入框和展示区域"""
        if index < 0: return

        # 健壮性检查
        if self.keywordCategorySelect is None: return

        category_key = self.keywordCategorySelect.itemData(index)
        if not category_key: return

        keywords = self.service.get_keywords_for_category(category_key)

        # 加载到输入框 (QTextEdit)
        if self.keywordInput:
            self.keywordInput.setText(", ".join(keywords))

        # 加载到展示区域 (QTextEdit，用于模拟标红效果)
        if self.currentKeywordsText:
            keywords_html = "".join(
                [f'<span style="color: blue; font-weight: bold; margin-right: 5px;">{kw}</span>' for kw in keywords])
            self.currentKeywordsText.setHtml(
                f'<div style="background-color: #eef; padding: 5px; border-radius: 5px;">{keywords_html}</div>')

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