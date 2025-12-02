# /Users/luckpuppy/Desktop/UItools/gemini/main.py

import sys
import os
# --- 路径修正代码 START ---
# 获取当前脚本 (main.py) 所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将此目录 (即 gemini 目录) 添加到 Python 搜索路径
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# --- 路径修正代码 END ---


from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QTabWidget, QWidget, QLabel
)
from PySide6.QtGui import QAction
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader

# 导入核心服务类 (通过 services/__init__.py 桥接导入)
# 保持不变，但现在它们指向拆分后的类
from gemini.services import QingShiluService

# 导入拆分后的模块
from gemini.ui_utils import load_ui_file # 从 gemini 目录导入
from gemini.widgets.single_tab import SingleTabWidget
from gemini.widgets.batch_tab import BatchTabWidget
from gemini.widgets.keyword_tab import KeywordTabWidget
from gemini.widgets.stats_tab import StatsTabWidget

# ... (其余代码保持不变) ...
# CategoryTabWidget (保持简单)
class CategoryTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        QLabel("分类管理 - 待实现", self)

# ... (MainWindow 类和其他代码保持不变) ...
# 注意：MainWindow 类中的 load_ui_file 需要从 ui_utils 导入，已修正


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

        # 转移主结构、Actions等
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

        # 转移 actions
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

    def _add_tab_modules(self):
        """实例化并添加所有 Tab 模块到 QTabWidget"""
        self.mainTabWidget.clear()

        # 【关键】将 QingShiluService 实例注入到各个 Tab 中
        self.single_tab = SingleTabWidget(self.qingshilu_service, self.mainTabWidget)
        self.mainTabWidget.addTab(self.single_tab, "1. 单条文本处理")

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
            if action_name in self.actions:
                self.actions[action_name].triggered.connect(
                    lambda checked, idx=index: self.mainTabWidget.setCurrentIndex(idx)
                )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    if window.ui_loaded:
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()