from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QScrollArea
from PySide6.QtCore import Signal, Qt

class FilterPanel(QWidget):
    filter_changed = Signal(dict)  # 发射当前选中的条件

    def __init__(self, title, options, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool)  # 工具窗口，不阻塞主窗口
        self.setWindowTitle(title)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 不抢焦点
        self.resize(200, 300)

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(5)

        self.checkboxes = {}
        for opt in options:
            cb = QCheckBox(opt)
            cb.stateChanged.connect(self.on_checkbox_changed)
            self.checkboxes[opt] = cb
            content_layout.addWidget(cb)

        content_layout.addStretch()

        # 存储当前选中的选项
        self.current_selection = []

    def on_checkbox_changed(self):
        selected = [opt for opt, cb in self.checkboxes.items() if cb.isChecked()]
        self.current_selection = selected
        # 发射信号，可以根据需要传递条件字典
        self.filter_changed.emit(self.get_criteria())

    def get_criteria(self):
        # 由子类实现具体条件转换，或者直接返回选中列表
        return self.current_selection

    def set_selection(self, selection):
        """外部设置选中项（用于重置等）"""
        for opt, cb in self.checkboxes.items():
            cb.setChecked(opt in selection)