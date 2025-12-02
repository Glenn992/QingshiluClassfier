from PySide6.QtWidgets import (
    QTextBrowser, QPushButton, QFileDialog, QComboBox, QLabel, QWidget
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QPalette

# 导入 ui_utils 中的 BaseTabWidget, WorkerThread (需要确保这些类是存在的)
from ui_utils import BaseTabWidget, WorkerThread


class StatsTabWidget(BaseTabWidget):
    # 🌟 新增：用于 HTML 渲染的自适应颜色属性 🌟
    EYE_CARE_COLOR = "#FFFFF0"
    TEXT_COLOR = "black"

    def __init__(self, qingshilu_service, parent=None):
        super().__init__("stats_tab.ui", parent)
        self.service = qingshilu_service

        # 🌟 关键：调用主题适应逻辑 🌟
        self.apply_theme_adaptation()

        # 假设 QingShiluService 将 DataModel 实例存储在名为 'model' 的属性中。
        self.category_structure = self.service.model.get_category_structure()

        # 当前选择的分类键
        self.current_l1_key = None
        self.current_l2_name = None
        self.current_l3_name = None

        # 存储 worker 线程实例，防止其被销毁导致程序崩溃 (SIGABRT)
        self.worker = None

        self.notificationLabel = None

        self._find_widgets()
        self._setup_ui_fixes()
        self.connect_signals()
        self._init_comboboxes()

        QTimer.singleShot(100, self.load_stats_data)

    # -----------------------------------------------------------
    # 🌟 新增：主题适应逻辑 🌟
    # -----------------------------------------------------------
    def apply_theme_adaptation(self):
        """
        根据系统主题，设置浅色模式下的背景色为米白色 (#FFFFF0)，
        深色模式下使用 Qt 的系统默认背景色，实现自适应。
        """
        palette = self.palette()

        # 获取系统窗口颜色作为判断依据
        window_color = palette.color(QPalette.Window)

        # 判断是否为深色模式：基于亮度的启发式判断
        is_dark_mode = window_color.red() < 128 and window_color.green() < 128 and window_color.blue() < 128

        if not is_dark_mode:
            # ☀️ 浅色模式：强制使用米白色 (#FFFFF0)
            custom_color = QColor("#FFFFF0")

            # 设置整个 Tab 顶层 Widget 的背景
            palette.setColor(QPalette.Window, custom_color)
            self.setAutoFillBackground(True)
            self.setPalette(palette)

            self.EYE_CARE_COLOR = "#FFFFF0"
            self.TEXT_COLOR = "black"
        else:
            # 🌙 深色模式：保持默认，跟随系统主题
            self.setAutoFillBackground(False)

            # 在深色模式下，使用系统背景色作为文本浏览器的背景
            dark_mode_bg_color = palette.color(QPalette.Base).name()  # 使用 Base 而非 Window 颜色作为内容区域背景
            self.EYE_CARE_COLOR = dark_mode_bg_color
            self.TEXT_COLOR = "white"  # 深色模式下文本颜色为白色

    def _find_widgets(self):
        """查找 UI 控件"""
        self.statsTextBrowser = self.findChild(QTextBrowser, "statsTextBrowser")
        self.exportCsvButton = self.findChild(QPushButton, "exportCsvButton")
        self.refreshButton = self.findChild(QPushButton, "refreshButton")
        self.level1ComboBox = self.findChild(QComboBox, "level1ComboBox")
        self.level2ComboBox = self.findChild(QComboBox, "level2ComboBox")
        self.level3ComboBox = self.findChild(QComboBox, "level3ComboBox")
        self.statsTitleLabel = self.findChild(QLabel, "statsTitleLabel")  # 确保标题标签被找到

        # 查找通知 QLabel
        self.notificationLabel = self.findChild(QLabel, "notificationLabel")
        if self.notificationLabel:
            self.notificationLabel.hide()  # 默认隐藏

        # 🌟 关键：对 statsTextBrowser 应用自适应样式 🌟
        if self.statsTextBrowser:
            # 设置 statsTextBrowser 的背景和文字颜色
            self.statsTextBrowser.setStyleSheet(
                f"""
                QTextBrowser {{
                    background-color: {self.EYE_CARE_COLOR}; 
                    color: {self.TEXT_COLOR};
                    border: 1px solid #ccc; 
                    padding: 10px;
                }}
                """
            )

        # 🌟 对 statsTitleLabel 重新设置 HTML 颜色以确保深色模式下可见 🌟
        if self.statsTitleLabel and self.TEXT_COLOR == "white":
            self.statsTitleLabel.setText(
                '<h2 style="color:white;">已分类条文统计与导出</h2>'
            )

    def _setup_ui_fixes(self):
        """修复：设置 ComboBox 的大小调整策略和最小宽度以确保长文本显示完整"""
        min_width = 180  # 增大最小宽度，更好地适应中文长文本

        if self.level1ComboBox:
            self.level1ComboBox.setMinimumWidth(min_width)
            # 允许根据内容自动调整宽度
            self.level1ComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        if self.level2ComboBox:
            self.level2ComboBox.setMinimumWidth(min_width)
            self.level2ComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        if self.level3ComboBox:
            self.level3ComboBox.setMinimumWidth(min_width)
            self.level3ComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

    def connect_signals(self):
        """连接信号槽"""
        if self.exportCsvButton:
            self.exportCsvButton.clicked.connect(self._handle_export_csv)
        if self.refreshButton:
            self.refreshButton.clicked.connect(self.load_stats_data)

        # 联动信号，使用 try-except 忽略未连接的警告
        if self.level1ComboBox:
            try:
                self.level1ComboBox.currentIndexChanged.disconnect(self._update_level2_combobox)
            except Exception:
                pass
            self.level1ComboBox.currentIndexChanged.connect(self._update_level2_combobox)

        if self.level2ComboBox:
            try:
                self.level2ComboBox.currentIndexChanged.disconnect(self._update_level3_combobox)
            except Exception:
                pass
            self.level2ComboBox.currentIndexChanged.connect(self._update_level3_combobox)

    def _init_comboboxes(self):
        """初始化一级分类下拉框"""
        self.level1ComboBox.blockSignals(True)
        self.level1ComboBox.clear()

        # 默认项：全部
        self.level1ComboBox.addItem("全部", None)

        # 从分类结构中添加一级分类
        for l1_key, l1_data in self.category_structure.items():
            l1_name = l1_data.get('name', str(l1_key))
            self.level1ComboBox.addItem(l1_name, l1_key)

        self.level1ComboBox.setCurrentIndex(0)
        self.level1ComboBox.blockSignals(False)

        self._update_level2_combobox()

    def _update_level2_combobox(self):
        """根据一级分类的选择更新二级分类下拉框"""
        self.level2ComboBox.blockSignals(True)
        self.level2ComboBox.clear()

        self.current_l1_key = self.level1ComboBox.currentData()

        self.level2ComboBox.addItem("全部", None)

        if self.current_l1_key is not None:
            l1_structure = self.category_structure.get(self.current_l1_key)
            if l1_structure:
                for l2_name in l1_structure.get('levels', {}).keys():
                    self.level2ComboBox.addItem(l2_name, l2_name)

        self.level2ComboBox.setCurrentIndex(0)
        self.level2ComboBox.blockSignals(False)
        self._update_level3_combobox()

    def _update_level3_combobox(self):
        """根据二级分类的选择更新三级分类下拉框"""
        self.level3ComboBox.blockSignals(True)
        self.level3ComboBox.clear()

        self.current_l2_name = self.level2ComboBox.currentData()

        self.level3ComboBox.addItem("全部", None)

        if self.current_l1_key is not None and self.current_l2_name is not None:
            l1_structure = self.category_structure.get(self.current_l1_key)
            if l1_structure:
                l2_structure = l1_structure.get('levels', {}).get(self.current_l2_name)

                if l2_structure:
                    for l3_name in l2_structure.keys():
                        self.level3ComboBox.addItem(l3_name, l3_name)

        self.level3ComboBox.setCurrentIndex(0)
        self.level3ComboBox.blockSignals(False)

        self.current_l3_name = self.level3ComboBox.currentData()
        self.load_stats_data()

    def _get_filter_key(self):
        """根据下拉框选择构造 Service 要求的筛选键"""
        l1_key = self.level1ComboBox.currentData()
        l2_name = self.level2ComboBox.currentData()
        l3_name = self.level3ComboBox.currentData()

        if l1_key is None:
            return None

        if l2_name is None:
            return str(l1_key)

        if l3_name is None:
            return f"{l1_key}/{l2_name}"

        return f"{l1_key}/{l2_name}/{l3_name}"

    def load_stats_data(self):
        """从 Service 获取分类数据并渲染统计信息 (根据筛选)"""
        filter_key = self._get_filter_key()

        try:
            stats_data = self.service.model.get_classified_stats(filter_key)
        except Exception as e:
            self.statsTextBrowser.setHtml(
                f"<h3 style='color:red;'>数据加载错误：</h3><p>请检查 service.model.get_classified_stats 方法和数据结构。错误信息：{e}</p>")
            return

        # 🌟 关键：使用自适应文本颜色 🌟
        text_color_style = f"color:{self.TEXT_COLOR};"

        # 调整 HTML 模板以使用自适应颜色
        # 标题颜色使用 #2d5a3e 保持视觉一致性，但基础文本颜色使用自适应的 self.TEXT_COLOR
        html = f'<h3 style="{text_color_style} color:#2d5a3e;">总计已分类条文: <span style="font-size: 1.2em;" id="total_count">0</span> 条</h3><hr style="border-color:{self.TEXT_COLOR};">'
        total_count = 0
        detail_html = f'<h4 style="margin-top: 15px; {text_color_style} color:#555;">当前筛选结果层级统计</h4>'

        if stats_data:
            for l1_key, l1_data in stats_data.items():
                l1_name = l1_data.get('name', f"L1 Key {l1_key}")
                l1_total = l1_data['count']
                total_count += l1_total

                # L1 标题
                detail_html += f'<div style="margin-top: 15px; {text_color_style}">'
                detail_html += f'<h4><b style="color:#1e40af;">[{l1_name}] ({l1_total} 条)</b></h4>'

                if 'levels' in l1_data:
                    detail_html += '<ul style="list-style: disc; margin-left: 20px;">'
                    for l2_name, l2_data in l1_data['levels'].items():
                        l2_count = l2_data['count']
                        # L2 列表项
                        detail_html += f'<li><b>{l2_name} ({l2_count} 条)</b>'

                        # L3 渲染
                        if 'levels' in l2_data and l2_data['levels']:
                            # L3 标签的背景色保持浅色（#e0f2fe）以增加对比度，字体用黑色
                            l3_bg_color = "#e0f2fe"
                            l3_text_color = "black"

                            detail_html += '<div style="margin-left: 20px; margin-top: 5px; line-height: 2.0;">'
                            l3_spans = []
                            for l3_name, l3_count in l2_data['levels'].items():
                                l3_spans.append(
                                    f'<span style="padding: 2px 5px; background-color: {l3_bg_color}; color:{l3_text_color}; border-radius: 4px; margin-right: 10px; white-space: nowrap;">{l3_name} ({l3_count} 条)</span>')

                            # 使用空格连接 span，让浏览器自动换行
                            detail_html += ' '.join(l3_spans)
                            detail_html += '</div>'

                        detail_html += "</li>"
                    detail_html += "</ul>"
                detail_html += "</div>"

        # 更新总计计数，然后拼接详细内容
        final_html = html.replace('<span style="font-size: 1.2em;" id="total_count">0</span>',
                                  f'<span style="font-size: 1.2em; color: #2d5a3e;">{total_count}</span>')
        final_html += detail_html

        if self.statsTextBrowser:
            self.statsTextBrowser.setHtml(final_html)

    # -----------------------------------------------------------
    # show_notification 方法
    # -----------------------------------------------------------
    def show_notification(self, message: str, type: str = 'info'):
        """显示临时的底部通知，3秒后自动隐藏 (取代 CustomToast)"""
        if not self.notificationLabel:
            return

        # 样式参考 BatchTabWidget，并略作美化调整
        style = "padding: 8px 15px; border-radius: 4px; font-weight: bold; text-align: center; margin-top: 5px;"

        # 定义颜色主题
        if type == 'error':
            # 红色主题
            style += "background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;"
        elif type == 'warning':
            # 黄色主题
            style += "background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;"
        elif type == 'success':
            # 成功主题 (绿色)
            style += "background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;"
        elif type == 'info':
            # 信息主题 (蓝色/灰色)
            style += "background-color: #e0f7fa; color: #004d40; border: 1px solid #b2ebf2;"
        else:
            # 默认主题
            style += "background-color: #e2e3e5; color: #383d41; border: 1px solid #d6d8db;"

        self.notificationLabel.setText(message)
        self.notificationLabel.setStyleSheet(style)
        self.notificationLabel.show()

        # 3秒后自动隐藏
        QTimer.singleShot(3000, self.notificationLabel.hide)

    # -----------------------------------------------------------
    # _handle_export_csv (使用 show_notification)
    # -----------------------------------------------------------
    def _handle_export_csv(self):
        """处理导出 CSV 按钮点击，导出当前筛选的结果"""
        filter_key = self._get_filter_key()

        # 根据筛选键生成默认文件名
        if filter_key is None:
            default_name = "classified_results_all.csv"
        else:
            default_name = f"classified_results_{filter_key.replace('/', '_')}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出分类结果", default_name, "CSV 文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            # 替换 CustomToast 为 show_notification (提示开始)
            self.show_notification("CSV 文件导出已在后台开始，请稍候...", type='info')

            # 将 worker 赋值给 self.worker，防止其被销毁
            self.worker = WorkerThread(
                self.service.model.export_classified_data_to_csv,
                file_path=file_path,
                filter_key=filter_key
            )
            # 使用 lambda 捕获结果，并调用辅助函数显示结果
            self.worker.result_signal.connect(lambda success: self._show_export_result(success, file_path))
            # 错误时使用 show_notification
            self.worker.error_signal.connect(lambda err: self.show_notification(
                f"导出失败：{err}", type='error'
            ))

            # 连接 finished 信号到 deleteLater，确保线程安全退出和清理
            self.worker.finished.connect(self.worker.deleteLater)

            self.worker.start()

    # -----------------------------------------------------------
    # _show_export_result (使用 show_notification)
    # -----------------------------------------------------------
    def _show_export_result(self, success, file_path):
        """显示导出结果 (使用 show_notification)"""
        if success:
            # 使用 show_notification
            self.show_notification(
                f"分类结果已成功导出到: {file_path}",
                type='success'
            )
        else:
            # 使用 show_notification
            self.show_notification(
                "没有数据可供导出，或导出失败。",
                type='warning'
            )
