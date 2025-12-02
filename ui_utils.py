# ui_utils.py

import os
import traceback
from PySide6.QtWidgets import (
    QWidget, QMessageBox, QFileDialog, QSizePolicy,
    QFrame, QVBoxLayout, QLabel, QHBoxLayout, QApplication
)
from PySide6.QtCore import (
    QFile, QIODevice, Qt, QThread, Signal, QCoreApplication, QTimer,
    QSize
)
from PySide6.QtGui import QFont, QPalette
from PySide6.QtUiTools import QUiLoader


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

def load_ui_file(loader, ui_filename, widget):
    # 假设 BaseTabWidget 或 MainWindow 在其 __init__ 中调用此函数

    # 【关键修正】使用 os.path.join 构造绝对路径
    # 获取当前项目的根目录 (即 gemini 目录)
    base_dir = os.path.dirname(os.path.abspath(__file__))  # 这假设 ui_utils.py 就在 gemini 根目录下

    # 构造 UI 文件的完整路径
    ui_path = os.path.join(base_dir, 'ui', ui_filename)

    ui_file = QFile(ui_path)
    if not ui_file.open(QIODevice.ReadOnly):
        # 如果文件加载失败，则弹出错误
        print(f"UI 文件加载失败: {ui_path}")
        QMessageBox.critical(widget, "加载错误", f"UI 文件未找到: {ui_path}")
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
            # 必须调用 deleteLater() 避免父对象持有无效子对象
            self.deleteLater()
            return

        # QCoreApplication.instance().installEventFilter(self) # 避免在UI加载时做过多事情
        self.loader.load(ui_file, self)
        ui_file.close()


# =======================================================
# CustomToast (新增) - 非阻塞式临时提醒
# =======================================================

class CustomToast(QFrame):
    """
    非阻塞式、浮动在屏幕上的临时提醒（Toast/Snackbar）。
    使用 QFrame 实现圆角和阴影效果。
    """

    def __init__(self, message, parent=None, duration=3000, type='info'):
        super().__init__(parent)
        # 允许浮动、无边框、位于顶层
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.BypassWindowManagerHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.duration = duration

        # 根据类型设置颜色
        if type == 'error':
            color = "#ef4444"  # 红色
        elif type in ('warning', 'warn'):
            color = "#f59e0b"  # 黄色
        elif type in ('info', 'success'):
            color = "#10b981"  # 绿色/信息
        else:
            color = "#6b7280"  # 灰色 (默认)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color}; 
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
                padding: 10px 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            QLabel {{
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
            }}
        """)

        # 布局
        layout = QHBoxLayout(self)
        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)
        self.setLayout(layout)

        # 确保 Toast 覆盖在父窗口上
        if parent:
            # 如果 parent 是 QWidget，找到它的顶层窗口 (MainWindow)
            self.parent_widget = parent.window() if isinstance(parent, QWidget) else parent
        else:
            self.parent_widget = QApplication.activeWindow() or None

        self.hide()

    def show_message(self):
        """显示 Toast 并在指定时间后隐藏"""
        self.adjustSize()

        if self.parent_widget and self.parent_widget.isVisible():
            # 定位在父窗口的底部中央
            parent_rect = self.parent_widget.geometry()

            # 计算位置：父窗口宽度中心 - Toast 自身宽度一半
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            # 定位在底部，向上偏移 30 像素
            y = parent_rect.y() + parent_rect.height() - self.height() - 30

            self.move(x, y)
        else:
            # 如果找不到活动的父窗口，显示在屏幕中央 (非推荐做法)
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = screen.height() - self.height() - 100
            self.move(x, y)

        self.show()

        # 使用 QTimer 设置定时隐藏
        QTimer.singleShot(self.duration, self.hide)
