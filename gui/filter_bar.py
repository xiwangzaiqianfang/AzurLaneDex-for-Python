from PySide6.QtWidgets import (QWidget, QHBoxLayout, QComboBox, QPushButton,
                               QLabel, QLineEdit, QMenu, QMessageBox,QDialog,
                               QInputDialog, QCompleter, QStyle, QToolButton)
from PySide6.QtCore import Signal, QStringListModel, QStringListModel
from PySide6.QtGui import QAction, Qt, QAction

class FilterBar(QWidget):
    filter_changed = Signal(dict)
    reset_clicked = Signal()
    stat_clicked = Signal()
    add_ship_clicked = Signal()
    switch_account_clicked = Signal() 
    export_user_state_clicked = Signal()
    import_user_state_overwrite_clicked = Signal()
    import_user_state_new_clicked = Signal()
    show_console_clicked = Signal()
    update_online_clicked = Signal()
    fleet_tech_clicked = Signal()
    theme_toggled = Signal()
    sort_order_changed = Signal(str, bool)
    batch_operation_signal = Signal(str, dict)
    export_static_clicked = Signal()
    import_static_clicked = Signal()

    def __init__(self, dev_mode=False, account_manager=None):
        self.dev_mode = dev_mode
        self.account_manager = account_manager
        super().__init__()
        self.setObjectName("filterBar")
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 排序选项
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "按编号排序", "按图鉴顺序排序", "按稀有度排序", "按名称排序",
            "按实装时间排序", "按改造日期排序", "按誓约排序", "按属性加成值排序"
        ])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        main_layout.addWidget(QLabel("排序:"))
        main_layout.addWidget(self.sort_combo)

        self.sort_reverse_btn = QPushButton("▼")
        self.sort_reverse_btn.setCheckable(True)
        self.sort_reverse_btn.clicked.connect(self.on_sort_changed)
        main_layout.addWidget(self.sort_reverse_btn)

        # 筛选按钮
        self.filter_btn = QPushButton("筛选")
        self.filter_btn.clicked.connect(self.toggle_filter_panel)
        main_layout.addWidget(self.filter_btn)
        
        # 搜索框
        self.search_edit = QLineEdit()
        search_icon = self.style().standardIcon(QStyle.SP_FileDialogContentsView)
        search_action = QAction(search_icon, "", self)
        self.search_edit.addAction(search_action, QLineEdit.LeadingPosition)
        self.search_edit.setPlaceholderText("搜索舰船名...")
        self.search_edit.textChanged.connect(self.emit_filter)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.search_edit.setCompleter(self.completer)
        self.completer.activated.connect(self.on_completer_activated)
        main_layout.addWidget(self.search_edit)

        # 重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_clicked)
        main_layout.addWidget(self.reset_btn)

        self.batch_btn = QToolButton()
        self.batch_btn.setText("批量操作")
        self.batch_btn.setPopupMode(QToolButton.InstantPopup)
        batch_menu = QMenu(self)
        self.batch_btn.setMenu(batch_menu)

        batch_actions = [
            ("设为已获得", "owned_true"),
            ("设为未获得", "owned_false"),
            ("设为已改造", "remodeled_true"),
            ("设为未改造", "remodeled_false"),
            ("设为已满破", "max_true"),
            ("设为未满破", "max_false"),
            ("设为已120级", "120_true"),
            ("设为未120级", "120_false"),
            ("设为已誓约", "oath_true"),
            ("设为未誓约", "oath_false"),
            ("设为已拥有特殊兵装", "special_gear_obtained_true"),
            ("设为未拥有特殊兵装", "special_gear_obtained_false"),
        ]
        for text, op in batch_actions:
            action = QAction(text, self)
            action.triggered.connect(lambda checked, op=op: self.batch_operation_signal.emit(op, self.get_current_criteria()))
            batch_menu.addAction(action)

        main_layout.addWidget(self.batch_btn)

        # 更多操作按钮
        self.more_btn = QPushButton("更多操作")
        self.more_btn.clicked.connect(self.show_more_menu)
        main_layout.addWidget(self.more_btn)

        main_layout.addStretch()

        self.filter_panel = None  # 高级筛选面板实例

    def emit_filter(self):
        """发射当前筛选条件（基础条件 + 高级面板条件）"""
        text = self.search_edit.text().strip()
        if text.startswith("[和谐名称] "):
            return  # 忽略带前缀的临时文本
        if text.startswith("[兵装] "):
            return  # 忽略带前缀的临时文本
        if text.startswith("[活动] "):
            return  # 忽略带前缀的临时文本
        if text.startswith("[获取方式] "):
            return  # 忽略带前缀的临时文本
        criteria = self.get_current_criteria()
        self.filter_changed.emit(criteria)

    def get_current_criteria(self):
        criteria = {}
        search_text = self.search_edit.text().strip()
        if search_text:
            criteria['name_contains'] = search_text
        if self.filter_panel is not None:
            criteria.update(self.filter_panel.get_criteria())
        return criteria

    def toggle_filter_panel(self):
        if self.filter_panel is None:
            from gui.advanced_filter_panel import AdvancedFilterPanel
            self.filter_panel = AdvancedFilterPanel(self.window())
            self.filter_panel.filter_changed.connect(self.emit_filter)
            btn_pos = self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft())
            self.filter_panel.move(btn_pos)
            self.filter_panel.show()
        else:
            if self.filter_panel.isVisible():
                self.filter_panel.hide()
            else:
                self.filter_panel.show()
                btn_pos = self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft())
                self.filter_panel.move(btn_pos)

    def reset(self):
        self.search_edit.clear()
        if self.filter_panel:
            self.filter_panel.reset()
        self.emit_filter()

    def show_more_menu(self):
        print("dev_mode:", self.dev_mode)
        print("account_manager:", self.account_manager)
        if self.account_manager:
            print("is_developer:", self.account_manager.is_developer())
        menu = QMenu(self)
        base_actions = [
            ("切换账户", self.switch_account_clicked),
            ("导出当前账户数据", self.export_user_state_clicked),
            ("导入数据并覆盖当前账户", self.import_user_state_overwrite_clicked),
            ("导入数据并创建新账户", self.import_user_state_new_clicked),
            ("显示终端", self.show_console_clicked),
        ]
        for text, signal in base_actions:
            action = QAction(text, self)
            if callable(signal):
                action.triggered.connect(signal)
            else:
                action.triggered.connect(signal.emit)
            menu.addAction(action)
        # 开发者专属操作（需要开发模式且当前账户为开发者）
        if self.dev_mode and self.account_manager and self.account_manager.is_developer():
            menu.addSeparator()
            dev_actions = [
                ("新建舰船", self.add_ship_clicked),
                ("导出静态数据", self.export_static_clicked),
                ("导入静态数据", self.import_static_clicked),
            ]
            for text, signal in dev_actions:
                action = QAction(text, self)
                action.triggered.connect(signal.emit)
                menu.addAction(action)
        menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().bottomLeft()))

    def set_ship_names(self, names):
        """设置搜索框的补全列表"""
        model = QStringListModel(names)
        self.completer.setModel(model)

    def set_completer_items(self, ship_names, alt_names, gear_names, event_names, acquire_keywords=None):
        """设置补全列表：舰船名 + 带前缀的兵装名"""
        items = []
        self.completer_map = {}
        for name in ship_names:
            items.append(name)
            self.completer_map[name] = name
        for name in alt_names:
            if name:
                display = f"[和谐名称] {name}"
                items.append(display)
                self.completer_map[display] = name
        for name in gear_names:
            if name:
                display = f"[兵装] {name}"
                items.append(display)
                self.completer_map[display] = name
        for name in event_names:
            if name:
                display = f"[活动] {name}"
                items.append(display)
                self.completer_map[display] = name
        if acquire_keywords:
            for kw in acquire_keywords:
                display = f"[获取方式] {kw}"
                items.append(display)
                self.completer_map[display] = kw
        model = QStringListModel(items)
        self.completer.setModel(model)

    def on_completer_activated(self, text):
        """处理补全项选择，去除前缀后设置搜索文本"""
        print(f"选中的文本: {text}")
        actual = self.completer_map.get(text, text)
        # 临时断开 textChanged 信号，避免递归
        self.search_edit.blockSignals(True)
        self.search_edit.setText(actual)
        self.search_edit.blockSignals(False)
        self.emit_filter()

    def on_sort_changed(self):
        index = self.sort_combo.currentIndex()
        reverse = self.sort_reverse_btn.isChecked()
        key_map = {
            0: "id",
            1: "game_order",
            2: "rarity",
            3: "name",
            4: "release_date",
            5: "remodel_date",
            6: "oath",
            7: "total_attr_bonus"
        }
        key = key_map.get(index, "id")
        self.sort_reverse_btn.setText("▲" if reverse else "▼")
        self.sort_order_changed.emit(key, reverse)

    def set_edit_password(self):
        if not hasattr(self, 'manager') or self.manager is None:
            QMessageBox.warning(self, "错误", "未设置管理器，无法修改密码。")
            return
        if self.manager.need_password_for_edit():
            old_pwd, ok = QInputDialog.getText(self, "验证原密码", "请输入当前编辑密码:", QLineEdit.Password)
            if not ok:
                return
            if not self.manager.verify_edit_password(old_pwd):
                QMessageBox.warning(self, "错误", "原密码错误，无法修改。")
                return
        new_pwd, ok = QInputDialog.getText(self, "设置编辑密码", 
                                       "请输入新密码（留空以清除）:", 
                                       QLineEdit.Password)
        if ok:
            self.manager.set_edit_password(new_pwd)
            if new_pwd:
                QMessageBox.information(self, "完成", "编辑密码已设置。")
            else:
                QMessageBox.information(self, "完成", "编辑密码已清除。")

    def open_settings(self):
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.open_settings()
        else:
            QMessageBox.warning(self, "错误", "无法打开设置页面。")

    def export_static_data(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "导出静态数据", "ships_static.json", "JSON (*.json)")
        if path:
            self.manager.export_static(path)
            QMessageBox.information(self, "完成", f"静态数据已导出至 {path}")

    def show_account_manager(self):
        from gui.account_dialog import AccountDialog
        dlg = AccountDialog(self.account_manager, self)
        if dlg.exec() == QDialog.Accepted:
            # 切换账户后重新加载数据并刷新界面
            self.manager.switch_account(self.account_manager.get_current_account())
            self.refresh_ui()   # 自定义刷新方法