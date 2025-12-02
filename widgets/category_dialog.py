# widgets/category_dialog.py

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QComboBox, QPushButton, QMessageBox
)

class CategorySelectionDialog(QDialog):
    # (代码与您 main.py 中的 CategorySelectionDialog 类完全相同)
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