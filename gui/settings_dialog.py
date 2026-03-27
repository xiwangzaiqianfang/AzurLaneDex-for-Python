# gui/settings_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QPushButton, QCheckBox, QGroupBox,
                               QLineEdit, QInputDialog, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QSettings
from manager import ShipManager

class SettingsDialog(QDialog):
    def __init__(self, manager: ShipManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("设置")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

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
        reset_btn = QPushButton("重置窗口大小")
        reset_btn.clicked.connect(self.reset_window_geometry)
        reset_layout.addWidget(reset_btn)
        reset_layout.addStretch()
        reset_layout.addWidget(reset_card)

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

        # 版本和作者信息
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(10, 10, 10, 10)
        #info_group = QGroupBox("关于")
        #info_layout = QVBoxLayout(info_group)
        info_title = QLabel("日志输出")
        info_title.setObjectName("cardTitle")
        info_layout.addWidget(QLabel("碧蓝航线图鉴"))
        version = self.manager.get_program_version()
        info_layout.addWidget(QLabel(f"版本: {version}"))
        info_layout.addWidget(QLabel("作者: 菲梦林光"))
        info_layout.addWidget(QLabel("遵循 CC BY-NC-SA 4.0 协议"))
        layout.addWidget(info_card)

        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # 加载当前主题设置
        self.load_theme_setting()

    def load_theme_setting(self):
        theme_mode = self.manager.config.get("theme_mode", "system")
        index = self.theme_combo.findText(theme_mode.capitalize())  # "system" -> "跟随系统"
        if index == -1:
            index = 0
        self.theme_combo.setCurrentIndex(index)

    def on_theme_changed(self):
        theme = self.theme_combo.currentText()
        print(f"[主题] 用户手动切换主题为: {theme}")
        if theme == "跟随系统":
            self.parent().set_system_theme_follow(True)
            self.manager.config["theme_mode"] = "system"
            self.manager.save_config()
        elif theme == "浅色":
            self.parent().set_manual_theme("light")
            self.manager.config["theme_mode"] = "light"
            #self.manager.current_theme = "light"
            self.manager.save_config()
        elif theme == "深色":
            self.parent().set_manual_theme("dark")
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
        self.parent().update_online()

    def on_log_toggled(self, checked):
        self.manager.config["log_edits"] = checked
        self.manager.save_config()

    def reset_window_geometry(self):
        # 调用主窗口的重置方法
        self.parent().reset_window_geometry()
        QMessageBox.information(self, "重置", "窗口大小已重置，下次启动将使用默认大小。")