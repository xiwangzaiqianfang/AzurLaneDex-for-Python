# gui/settings_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QPushButton, QCheckBox, QGroupBox,
                               QLineEdit, QInputDialog, QFrame, QMessageBox, QScrollArea, QWidget)
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from manager import ShipManager

class SettingsPage(QWidget):
    def __init__(self, manager: ShipManager, main_window):
        super().__init__()
        self.manager = manager
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setSpacing(10)
         # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        app_card = QFrame()
        app_card.setObjectName("card")
        app_layout = QVBoxLayout(app_card)
        app_layout.setContentsMargins(15, 15, 15, 15)
        app_layout.setAlignment(Qt.AlignCenter)
        app_layout.setSpacing(15)
        logo_label = QLabel()
        pixmap = QPixmap("app_icon.ico").scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        app_layout.addWidget(logo_label)

        name_label = QLabel("碧蓝航线图鉴")
        name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        app_layout.addWidget(name_label)
        name_label.setAlignment(Qt.AlignCenter)
        #app_layout.addStretch()
        layout.addWidget(app_card)

        # 主题设置
        theme_card = QFrame()
        theme_card.setObjectName("card")
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(10, 10, 10, 10)
        #theme_group = QGroupBox("主题")
        #theme_layout = QHBoxLayout(theme_group)
        theme_title = QLabel("主题")
        theme_title.setObjectName("cardTitle")
        theme_title.setStyleSheet("font-weight: bold;")
        theme_layout.addWidget(theme_title)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["跟随系统", "浅色", "深色"])
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(QLabel("界面主题:"))
        theme_layout.addWidget(self.theme_combo)
        # 禁用鼠标滚轮更改选项
        self.theme_combo.wheelEvent = lambda event: None
        theme_layout.addStretch()
        layout.addWidget(theme_card)

        # 密码设置
        pwd_card = QFrame()
        pwd_card.setObjectName("card")
        pwd_layout = QVBoxLayout(pwd_card)
        pwd_layout.setContentsMargins(10, 10, 10, 10)
        #pwd_group = QGroupBox("编辑密码")
        #pwd_layout = QHBoxLayout(pwd_group)
        pwd_title = QLabel("编辑密码")
        pwd_title.setObjectName("cardTitle")
        pwd_title.setStyleSheet("font-weight: bold;")
        pwd_layout.addWidget(pwd_title)
        self.pwd_btn = QPushButton("修改编辑密码")
        self.pwd_btn.clicked.connect(self.change_password)
        pwd_layout.addWidget(self.pwd_btn)
        pwd_layout.addStretch()
        layout.addWidget(pwd_card)

        reset_card = QFrame()
        reset_card.setObjectName("card")
        reset_layout = QVBoxLayout(reset_card)
        reset_layout.setContentsMargins(10, 10, 10, 10)
        reset_title = QLabel("窗口尺寸")
        reset_title.setObjectName("cardTitle")
        reset_title.setStyleSheet("font-weight: bold;")
        reset_layout.addWidget(reset_title)
        self.reset_btn = QPushButton("重置窗口大小")
        self.reset_btn.clicked.connect(self.reset_window_geometry)
        reset_layout.addWidget(self.reset_btn)
        reset_layout.addStretch()
        layout.addWidget(reset_card)

        # 网络更新
        update_card = QFrame()
        update_card.setObjectName("card")
        update_layout = QVBoxLayout(update_card)
        update_layout.setContentsMargins(10, 10, 10, 10)
        #update_group = QGroupBox("数据更新")
        #update_layout = QHBoxLayout(update_group)
        update_title = QLabel("更新")
        update_title.setObjectName("cardTitle")
        update_title.setStyleSheet("font-weight: bold;")
        update_layout.addWidget(update_title)
        self.update_btn = QPushButton("从网络更新舰船数据")
        self.update_btn.clicked.connect(self.update_data)
        update_layout.addWidget(self.update_btn)
        update_layout.addStretch()
        layout.addWidget(update_card)

        # 日志记录
        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(10, 10, 10, 10)
        #log_group = QGroupBox("日志")
        #log_layout = QHBoxLayout(log_group)
        log_title = QLabel("日志输出")
        log_title.setObjectName("cardTitle")
        log_title.setStyleSheet("font-weight: bold;")
        log_layout.addWidget(log_title)
        self.log_cb = QCheckBox("记录编辑操作日志")
        self.log_cb.setChecked(self.manager.config.get("log_edits", True))
        self.log_cb.toggled.connect(self.on_log_toggled)
        log_layout.addWidget(self.log_cb)
        log_layout.addStretch()
        layout.addWidget(log_card)

        # ---- 关于卡片（可展开） ----
        about_card = QFrame()
        about_card.setObjectName("card")
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(10, 10, 10, 10)

        # 标题行（包含展开按钮）
        self.about_btn = QPushButton()
        self.about_btn.setFlat(True)
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.setStyleSheet("text-align: left; background: transparent; border: none;")
        btn_layout = QHBoxLayout(self.about_btn)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        about_title = QLabel("关于")
        about_title.setObjectName("cardTitle")
        btn_layout.addWidget(about_title)
        btn_layout.addStretch()
        self.about_arrow = QLabel("▼")
        btn_layout.addWidget(self.about_arrow)

        about_layout.addWidget(self.about_btn)

        # 可展开的内容区域
        self.about_content = QWidget()
        self.about_content.setVisible(False)
        about_content_layout = QVBoxLayout(self.about_content)
        about_content_layout.setContentsMargins(0, 10, 0, 0)

        version = getattr(self.manager, 'get_program_version', lambda: "1.0.0")()
        about_content_layout.addWidget(QLabel(f"版本: {version}"))
        about_content_layout.addWidget(QLabel("作者: 菲梦林光"))
        about_content_layout.addWidget(QLabel("开源协议: CC BY-NC-SA 4.0"))
        about_content_layout.addWidget(QLabel("项目主页: https://github.com/xiwangzaiqianfang/AzurLane-Dex"))
        about_content_layout.addWidget(QLabel("本软件所有舰船数据均来自“碧蓝航线Wiki”"))
        
        about_content_layout.addStretch()
        about_layout.addWidget(self.about_content)
        layout.addWidget(about_card)
        self.about_btn.clicked.connect(self.toggle_about)

        # 加载当前主题设置
        self.load_theme_setting()

    def load_theme_setting(self):
        theme_mode = self.manager.config.get("theme_mode", "system")
        if theme_mode == "system":
            self.theme_combo.setCurrentIndex(0)
        elif theme_mode == "light":
            self.theme_combo.setCurrentIndex(1)
        elif theme_mode == "dark":
            self.theme_combo.setCurrentIndex(2)
        #index = self.theme_combo.findText(theme_mode.capitalize())  # "system" -> "跟随系统"
        #if index == -1:
        #    index = 0
        #self.theme_combo.setCurrentIndex(index)

    def on_theme_changed(self):
        theme = self.theme_combo.currentText()
        print(f"[主题] 用户手动切换主题为: {theme}")
        if theme == "跟随系统":
            self.window().set_system_theme_follow(True)
            self.manager.config["theme_mode"] = "system"
            #self.manager.save_config()
        elif theme == "浅色":
            self.window().set_manual_theme("light")
            self.manager.config["theme_mode"] = "light"
            #self.manager.current_theme = "light"
            #self.manager.save_config()
        elif theme == "深色":
            self.window().set_manual_theme("dark")
            self.manager.config["theme_mode"] = "dark"
            #self.manager.current_theme = "dark"
        self.manager.save_config()

    def change_password(self):
        from PySide6.QtWidgets import QInputDialog, QLineEdit
        # 先验证旧密码
        if self.manager.need_password_for_edit():
            old_pwd, ok = QInputDialog.getText(self, "验证原密码", "请输入当前编辑密码:", QLineEdit.Password)
            if not ok or not self.manager.verify_edit_password(old_pwd):
                QMessageBox.warning(self, "错误", "原密码错误")
                return
        new_pwd, ok = QInputDialog.getText(self, "设置新密码", "请输入新密码（留空清除）:", QLineEdit.Password)
        if ok:
            self.manager.set_edit_password(new_pwd)
            if new_pwd:
                QMessageBox.information(self, "完成", "编辑密码已设置")
            else:
                QMessageBox.information(self, "完成", "编辑密码已清除")

    def update_data(self):
        # 调用主窗口的更新方法
        self.window().update_online()

    def on_log_toggled(self, checked):
        self.manager.config["log_edits"] = checked
        self.manager.save_config()

    def reset_window_geometry(self):
        # 调用主窗口的重置方法
        self.window().reset_window_geometry()
        QMessageBox.information(self, "重置", "窗口大小已重置，下次启动将使用默认大小。")

    def toggle_about(self):
        visible = not self.about_content.isVisible()
        self.about_content.setVisible(visible)
        self.about_arrow.setText("▲" if visible else "▼")