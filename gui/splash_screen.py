from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 300)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # 应用图标
        icon_label = QLabel()
        pixmap = QPixmap("app_icon.ico")  # 替换为您的图标路径
        if not pixmap.isNull():
            pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # 加载文字
        self.text_label = QLabel("正在加载舰船数据...")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("color: #0078d4; font-size: 14px;")
        layout.addWidget(self.text_label)

        # 进度条（循环动画）
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为繁忙模式（无限循环）
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedWidth(200)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        # 居中显示
        self.center()

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())

    def set_message(self, text):
        self.text_label.setText(text)