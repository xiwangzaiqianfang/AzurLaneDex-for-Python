# gui/console_widget.py
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, QObject,Qt
from PySide6.QtGui import QTextCursor

class StreamRedirector(QObject):
    """将写入的数据通过信号发射到 GUI"""
    new_text = Signal(str)

    def write(self, text):
        if text.strip():
            self.new_text.emit(text)

    def flush(self):
        pass

class ConsoleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("终端输出")
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        # 文本显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.text_edit)

        # 按钮栏
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_output)
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.hide)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        # 设置重定向
        self.redirector = StreamRedirector()
        self.redirector.new_text.connect(self.append_text)

        # 保存原始的 stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # 重定向
        sys.stdout = self.redirector
        sys.stderr = self.redirector

    def append_text(self, text):
        """在文本显示区追加内容并滚动到底部"""
        self.text_edit.moveCursor(QTextCursor.End)
        if not text.endswith('\n'):
            text += '\n'
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def clear_output(self):
        self.text_edit.clear()

    def restore_std(self):
        """恢复原始的 stdout/stderr"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def closeEvent(self, event):
        self.restore_std()
        super().closeEvent(event)