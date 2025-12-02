# main.py
# 主程序入口：负责 UI 加载、模块组装和信号连接 (View/Controller/Coordinator)

import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QWidget, QLabel, QTextEdit, QPushButton,
    QMenuBar, QStatusBar, QTabWidget, QVBoxLayout
)
from PySide6.QtGui import QAction
from PySide6.QtCore import QFile, QIODevice, Qt
from PySide6.QtUiTools import QUiLoader

# 【关键变化】从 services 文件导入核心服务类
from services import AnalysisService, FileManager


# --- 辅助函数：改进的 QUiLoader 文件打开逻辑 (已更新路径) ---
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


# =======================================================
# 模块化 Tab 类 (View/Controller 层)
# =======================================================

class BaseTabWidget(QWidget):
    """所有 Tab 模块的基类，包含加载自身的 UI 逻辑"""

    def __init__(self, ui_file_name, parent=None):
        super().__init__(parent)
        self.loader = QUiLoader()
        self.ui_file_name = ui_file_name
        self.load_ui()

    def load_ui(self):
        # 调用更新后的 load_ui_file，它现在会查找 ui/ 目录
        ui_file = load_ui_file(self.loader, self.ui_file_name, self)
        if ui_file is None:
            return
        self.loader.load(ui_file, self)
        ui_file.close()


# -------------------------------------------------------------
# 1. 单条文本处理 Tab (View/Controller 职责)
# -------------------------------------------------------------
class SingleTabWidget(BaseTabWidget):
    def __init__(self, parent=None):
        super().__init__("single_tab.ui", parent)
        # 实例化 Service 类
        self.analysis_service = AnalysisService()
        self.connect_signals()
        self._update_char_count_controller()  # 初始化字符计数

    def connect_signals(self):
        # 组件查找：View/Controller 负责连接 UI 组件
        self.originalTextEdit = self.findChild(QTextEdit, "originalTextEdit")
        self.translationTextEdit = self.findChild(QTextEdit, "translationTextEdit")
        self.charCountLabel = self.findChild(QLabel, "charCountLabel")
        self.clearButton = self.findChild(QPushButton, "clearButton")
        self.analyzeButton = self.findChild(QPushButton, "analyzeButton")
        self.copyButton = self.findChild(QPushButton, "copyButton")

        # 连接逻辑
        if self.originalTextEdit:
            self.originalTextEdit.textChanged.connect(self._update_char_count_controller)
        if self.clearButton and self.originalTextEdit:
            self.clearButton.clicked.connect(self.originalTextEdit.clear)
        if self.analyzeButton:
            self.analyzeButton.clicked.connect(self._smart_analyze_controller)
        if self.copyButton:
            self.copyButton.clicked.connect(self._copy_translation_controller)

        # 占位功能连接 (保持不变)
        self.findChild(QPushButton, "saveClassificationButton").clicked.connect(
            lambda: QMessageBox.information(self, "功能", "保存分类功能待实现..."))
        self.findChild(QPushButton, "saveTranslationButton").clicked.connect(
            lambda: QMessageBox.information(self, "功能", "保存翻译功能待实现..."))
        self.findChild(QPushButton, "resetClassificationButton").clicked.connect(
            lambda: QMessageBox.information(self, "功能", "重置分类功能待实现..."))

    # View/Controller 方法：仅负责 UI 状态更新和 Service 调用
    def _update_char_count_controller(self):
        if self.originalTextEdit and self.charCountLabel:
            count = len(self.originalTextEdit.toPlainText())
            self.charCountLabel.setText(f"{count} 字符")

    def _smart_analyze_controller(self):
        text = self.originalTextEdit.toPlainText()

        if not text:
            QMessageBox.warning(self, "输入为空", "请输入原文内容进行分析。")
            return

        # *** Controller 调用 Service 层的核心逻辑 ***
        translation_text = self.analysis_service.analyze_text(text)

        # Controller 根据 Service 返回的结果更新 UI
        if translation_text:
            self.translationTextEdit.setText(translation_text)
            QMessageBox.information(self, "分析完成", "智能分析已完成。")
        else:
            QMessageBox.warning(self, "分析失败", "分析服务返回空结果。")

    def _copy_translation_controller(self):
        if self.translationTextEdit:
            self.translationTextEdit.selectAll()
            self.translationTextEdit.copy()
            QMessageBox.information(self, "复制成功", "译文已复制到剪贴板。")


# -------------------------------------------------------------
# 2. 批量处理 Tab (View/Controller 职责)
# -------------------------------------------------------------
class BatchTabWidget(BaseTabWidget):
    def __init__(self, parent=None):
        super().__init__("batch_tab.ui", parent)
        # 实例化 Service 类
        self.file_manager = FileManager()
        self.connect_signals()

    def connect_signals(self):
        self.selectBatchFileButton = self.findChild(QPushButton, "selectBatchFileButton")
        self.processBatchButton = self.findChild(QPushButton, "processBatchButton")
        self.saveBatchButton = self.findChild(QPushButton, "saveBatchButton")

        if self.selectBatchFileButton:
            self.selectBatchFileButton.clicked.connect(self._handle_select_batch_files_controller)
        if self.processBatchButton:
            self.processBatchButton.clicked.connect(self._handle_process_batch_files_controller)
        if self.saveBatchButton:
            self.saveBatchButton.clicked.connect(
                lambda: QMessageBox.information(self, "功能", "批量保存结果功能待实现..."))

    # View/Controller 方法：仅处理 UI 交互和 Service 调用
    def _handle_select_batch_files_controller(self):
        """处理选择批量文件按钮的点击事件 (Controller 职责)"""

        # *** Controller 调用 Service 层的方法获取文件列表 ***
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
            else:
                QMessageBox.warning(self, "警告", "UI加载错误：未找到 batchListLayout。")

    def _handle_process_batch_files_controller(self):
        """处理批量分析按钮的点击事件 (Controller 职责)"""
        if not self.file_manager.get_selected_files():
            QMessageBox.warning(self, "警告", "请先选择需要处理的文件。")
            return

        # *** Controller 调用 Service 层的方法执行核心逻辑 ***
        self.file_manager.process_files()


# -------------------------------------------------------------
# 3/4/5. 关键词/统计/分类 Tab (占位模块, 保持不变)
# -------------------------------------------------------------
class KeywordTabWidget(BaseTabWidget):
    def __init__(self, parent=None):
        super().__init__("keyword_tab.ui", parent)


class StatsTabWidget(BaseTabWidget):
    def __init__(self, parent=None):
        super().__init__("stats_tab.ui", parent)


class CategoryTabWidget(BaseTabWidget):
    def __init__(self, parent=None):
        super().__init__("category_tab.ui", parent)


# =======================================================
# 主窗口 (Coordinator, 保持不变)
# =======================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loader = QUiLoader()
        self.ui_loaded = False

        # --- 1. 加载主窗口外壳 ---
        # 注意这里调用了更新路径后的 load_ui_file
        ui_file = load_ui_file(self.loader, "main_window.ui", self)
        if ui_file is None: return

        # 使用 temp_window 模式加载和转移主结构 (保持不变)
        temp_window = self.loader.load(ui_file)
        ui_file.close()

        if temp_window is None:
            QMessageBox.critical(self, "加载错误", "无法从 main_window.ui 加载内容。")
            return

        # 转移 Central Widget、MenuBar、StatusBar
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
        # 收集所有 Action
        for action_name in ["actionGoToSingle", "actionGoToBatch", "actionGoToKeyword", "actionGoToStatistics",
                            "actionGoToCategory"]:
            action = temp_window.findChild(QAction, action_name)
            if action:
                action.setParent(self)
                self.actions[action_name] = action

        # 销毁临时窗口
        temp_window.deleteLater()
        self.ui_loaded = True

        # --- 2. 组装 Tab 模块 (Composition) ---
        self.mainTabWidget = self.findChild(QTabWidget, "mainTabWidget")
        if self.mainTabWidget:
            self._add_tab_modules()
            self._connect_menu_actions()

    def _add_tab_modules(self):
        """实例化并添加所有 Tab 模块到 QTabWidget"""
        self.mainTabWidget.clear()

        self.single_tab = SingleTabWidget(self.mainTabWidget)
        self.mainTabWidget.addTab(self.single_tab, "1. 单条文本处理")

        self.batch_tab = BatchTabWidget(self.mainTabWidget)
        self.mainTabWidget.addTab(self.batch_tab, "2. 批量处理")

        self.keyword_tab = KeywordTabWidget(self.mainTabWidget)
        self.mainTabWidget.addTab(self.keyword_tab, "3. 关键词管理")

        self.stats_tab = StatsTabWidget(self.mainTabWidget)
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