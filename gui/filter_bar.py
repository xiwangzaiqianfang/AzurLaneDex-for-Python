from PySide6.QtWidgets import (QWidget, QHBoxLayout, QComboBox, QCheckBox, QPushButton, QLabel, QLineEdit, QToolButton, QMenu, QStyle, QCompleter)
from PySide6.QtCore import Signal, QStringListModel
from PySide6.QtGui import QAction, QIcon, QFont, QFontDatabase, Qt
import os
import hashlib
from manager import ShipManager
from gui.advanced_filter_panel import AdvancedFilterPanel

class FilterBar(QWidget):
    filter_changed = Signal(dict)
    reset_clicked = Signal()
    stat_clicked = Signal()
    add_ship_clicked = Signal()
    switch_file_clicked = Signal()
    export_clicked = Signal()
    import_clicked = Signal()
    update_online_clicked = Signal()
    fleet_tech_clicked = Signal()
    theme_toggled = Signal()
    sort_order_changed = Signal(str, bool)
    batch_operation_signal = Signal(str, dict)   # (operation, criteria)

    def __init__(self):
        super().__init__()
        self.manager = None
        self.main_window = None
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 常用按钮
        row1 = QHBoxLayout()
        row1.setSpacing(5)
        # 阵营
        row1.addWidget(QLabel("阵营:"))
        self.faction_combo = QComboBox()
        self.faction_combo.wheelEvent = lambda event: None
        self.faction_combo.addItems(["全部", "白鹰", "皇家", "重樱", "铁血", "东煌", "撒丁帝国", "北方联合", "自由鸢尾", "维希教廷", "META", "其他"])
        self.faction_combo.currentTextChanged.connect(self.on_filter_changed)
        row1.addWidget(self.faction_combo)

        # 舰种
        row1.addWidget(QLabel("舰种:"))
        self.class_combo = QComboBox()
        self.class_combo.wheelEvent = lambda event: None
        self.class_combo.addItems(["全部", "驱逐", "轻巡", "重巡", "超巡", "战巡", "战列", "航母", "轻航", "航战", "重炮", "维修", "潜艇", "潜母", "其他"])
        self.class_combo.currentTextChanged.connect(self.on_filter_changed)
        row1.addWidget(self.class_combo)

        # 稀有度
        row1.addWidget(QLabel("稀有度:"))
        self.rarity_combo = QComboBox()
        self.rarity_combo.wheelEvent = lambda event: None
        self.rarity_combo.addItems(["全部", "普通", "稀有", "精锐", "超稀有", "海上传奇"])
        self.rarity_combo.currentTextChanged.connect(self.on_filter_changed)
        row1.addWidget(self.rarity_combo)

        # 排序方式
        self.sort_combo = QComboBox()
        self.sort_combo.wheelEvent = lambda event: None
        self.sort_combo.addItems(["按编号", "按名称", "按稀有度", "按誓约", "按图鉴顺序", "按实装时间"])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        row1.addWidget(QLabel("排序:"))
        row1.addWidget(self.sort_combo)

        # 升序/降序按钮
        self.sort_reverse_btn = QPushButton("▼")
        self.sort_reverse_btn.setFixedSize(30, 25)
        self.sort_reverse_btn.setCheckable(True)
        self.sort_reverse_btn.clicked.connect(self.on_sort_changed)
        row1.addWidget(self.sort_reverse_btn)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索舰船名...")
        #icon_font = QFont(icon_font_family, 10)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)          # 忽略大小写
        self.completer.setFilterMode(Qt.MatchContains)                 # 包含匹配（可选）
        self.search_edit.setCompleter(self.completer)
        search_icon = self.style().standardIcon(QStyle.SP_FileDialogContentsView)
        search_action = QAction(search_icon, "", self)  # 先创建空动作
        #icon_font = QFont("Segoe Fluent Icons", search_action.font().pointSize())
        #search_action.setFont(icon_font)
        #search_action.setText("")   # 搜索图标字符    
        #search_action.setToolTip("搜索")
        self.search_edit.addAction(search_action, QLineEdit.LeadingPosition)
        self.search_edit.textChanged.connect(self.on_filter_changed)
        row1.addWidget(self.search_edit)

        # 折叠高级筛选按钮
        self.adv_btn = QPushButton("高级筛选")
        self.adv_btn.clicked.connect(self.toggle_advanced_panel)
        row1.addWidget(self.adv_btn)

        # 按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_clicked)
        row1.addWidget(self.reset_btn)

        self.batch_btn = QToolButton()
        self.batch_btn.setText("批量操作")
        self.batch_btn.setPopupMode(QToolButton.InstantPopup)
        batch_menu = QMenu(self)
        self.batch_btn.setMenu(batch_menu)

        # 添加菜单项
        action_set_owned_true = QAction("设为已获得", self)
        action_set_owned_true.triggered.connect(self.batch_set_owned_true)
        batch_menu.addAction(action_set_owned_true)

        action_set_owned_false = QAction("设为未获得", self)
        action_set_owned_false.triggered.connect(self.batch_set_owned_false)
        batch_menu.addAction(action_set_owned_false)

        action_set_oath_true = QAction("设为誓约", self)
        action_set_oath_true.triggered.connect(self.batch_set_oath_true)
        batch_menu.addAction(action_set_oath_true)

        action_set_oath_false = QAction("取消誓约", self)
        action_set_oath_false.triggered.connect(self.batch_set_oath_false)
        batch_menu.addAction(action_set_oath_false)

        # 满破（突破数=3）
        action_set_max_true = QAction("设为满破", self)
        action_set_max_true.triggered.connect(self.batch_set_max_true)
        batch_menu.addAction(action_set_max_true)

        action_set_max_false = QAction("取消满破", self)
        action_set_max_false.triggered.connect(self.batch_set_max_false)
        batch_menu.addAction(action_set_max_false)

        # 120级
        action_set_120_true = QAction("设为120级", self)
        action_set_120_true.triggered.connect(self.batch_set_120_true)
        batch_menu.addAction(action_set_120_true)

        action_set_120_false = QAction("取消120级", self)
        action_set_120_false.triggered.connect(self.batch_set_120_false)
        batch_menu.addAction(action_set_120_false)

        # 改造（仅对可改造船有效，但批量时直接设置）
        action_set_remodeled_true = QAction("设为已改造", self)
        action_set_remodeled_true.triggered.connect(self.batch_set_remodeled_true)
        batch_menu.addAction(action_set_remodeled_true)

        action_set_remodeled_false = QAction("取消改造", self)
        action_set_remodeled_false.triggered.connect(self.batch_set_remodeled_false)
        batch_menu.addAction(action_set_remodeled_false)

        row1.addWidget(self.batch_btn)

        # 创建“更多操作”按钮
        #self.base_text = "更多操作"
        self.more_btn = QToolButton()
        self.more_btn.setObjectName("more_btn")
        self.more_btn.setText("更多操作")
        #self.more_btn.setText(self.base_text + "")
        #icon_font = QFont("Segoe Fluent Icons", self.more_btn.font().pointSize())
        #self.more_btn.setFont(icon_font)
        self.more_btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self)
        self.more_btn.setMenu(menu)
        #menu.aboutToShow.connect(self.on_more_menu_shown)
        #menu.aboutToHide.connect(self.on_more_menu_hidden)

        # 添加菜单项
        action_add_ship = QAction("新建舰船", self)
        action_add_ship.triggered.connect(self.add_ship_clicked.emit)
        menu.addAction(action_add_ship)

        action_switch_file = QAction("切换账号", self)
        action_switch_file.triggered.connect(self.switch_file_clicked.emit)
        menu.addAction(action_switch_file)


        action_export = QAction("导出数据", self)
        action_export.triggered.connect(self.export_clicked.emit)
        menu.addAction(action_export)

        action_import = QAction("导入数据", self)
        action_import.triggered.connect(self.import_clicked.emit)
        menu.addAction(action_import)

        row1.addWidget(self.more_btn)

        row1.addStretch()
        main_layout.addLayout(row1)

        self.adv_panel = None

    def toggle_advanced_panel(self):
        if self.adv_panel is None:
            from .advanced_filter_panel import AdvancedFilterPanel
            # 只传递 parent 参数，不传递第一个参数（默认为 None）
            self.adv_panel = AdvancedFilterPanel(parent=self.window())
            self.adv_panel.filter_changed.connect(self.on_advanced_filter_changed)
            btn_pos = self.adv_btn.mapToGlobal(self.adv_btn.rect().bottomLeft())
            self.adv_panel.move(btn_pos)
            self.adv_panel.show()
        else:
            if self.adv_panel.isVisible():
                self.adv_panel.hide()
            else:
                self.adv_panel.show()
                btn_pos = self.adv_btn.mapToGlobal(self.adv_btn.rect().bottomLeft())
                self.adv_panel.move(btn_pos)

    def on_filter_changed(self):
        #print("on_filter_changed 被调用")
        criteria = self.get_criteria()
        if self.faction_combo.currentText() != "全部":
            criteria['faction'] = self.faction_combo.currentText()
        if self.class_combo.currentText() != "全部":
            criteria['ship_class'] = self.class_combo.currentText()
        if self.rarity_combo.currentText() != "全部":
            criteria['rarity'] = self.rarity_combo.currentText()
        self.filter_changed.emit(criteria)

    def reset(self):
        self.faction_combo.setCurrentText("全部")
        self.class_combo.setCurrentText("全部")
        self.rarity_combo.setCurrentText("全部")
        self.sort_combo.setCurrentIndex(0)
        self.sort_reverse_btn.setChecked(False)
        self.search_edit.clear()
        if self.adv_panel and self.adv_panel.isVisible():
            self.adv_panel.remodel_cb.setChecked(False)
            self.adv_panel.remodeled_cb.setChecked(False)
            self.adv_panel.oath_cb.setChecked(False)
            self.adv_panel.owned_cb.setChecked(False)
            self.adv_panel.max_cb.setChecked(False)
            self.adv_panel.level120_cb.setChecked(False)
            self.adv_panel.not_owned_cb.setChecked(False)
            self.adv_panel.not_max_cb.setChecked(False)
            self.adv_panel.not_level120_cb.setChecked(False)
            self.adv_panel.can_remodel_not_cb.setChecked(False)

    def on_advanced_filter_changed(self, adv_criteria):
        """高级面板的筛选条件变化时，与基础条件合并后发射"""
        #print("接收到高级条件:", adv_criteria)
        base = self.get_criteria()
        #print("基础条件:", base)
        combined = base.copy()
        combined.update(adv_criteria)
        #print("合并后的筛选条件:", combined)
        self.filter_changed.emit(combined)

    def get_criteria(self):
        # 返回当前筛选条件字典，用于刷新时重新应用
        criteria = {}
        search_text = self.search_edit.text().strip()
        if search_text:
            criteria['name_contains'] = search_text
        if self.faction_combo.currentText() != "全部":
            criteria['faction'] = self.faction_combo.currentText()
        if self.class_combo.currentText() != "全部":
            criteria['ship_class'] = self.class_combo.currentText()
        if self.rarity_combo.currentText() != "全部":
            criteria['rarity'] = self.rarity_combo.currentText()
        return criteria
    
    def set_ship_names(self, names):
        """设置补全用的舰船名称列表"""
        model = QStringListModel(names)
        self.completer.setModel(model)
    
    def open_advanced_filter(self):
        from .advanced_filter_panel import AdvancedFilterDialog
        dlg = AdvancedFilterDialog(self.get_criteria(), self)
        dlg.filter_applied.connect(self.on_advanced_filter_applied)
        dlg.exec_()

    def on_sort_changed(self):
        """排序选项变化时发射信号"""
        index = self.sort_combo.currentIndex()
        reverse = self.sort_reverse_btn.isChecked()
        # 映射下拉选项到 manager.sort 的 key
        key_map = {
            0: "id",
            1: "name",
            2: "rarity",
            3: "oath",
            4: "game_order",
            5: "release_date"
        }
        key = key_map.get(index, "id")
        self.sort_reverse_btn.setText("▲" if reverse else "▼")
        self.sort_order_changed.emit(key, reverse)

    def set_edit_password(self):
        from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
        if not self.manager:
            return
        if self.manager.need_password_for_edit():
            # 请求原密码
            old_pwd, ok = QInputDialog.getText(self, "验证原密码", "请输入当前编辑密码:", QLineEdit.Password)
            if not ok:
                return
            if not self.manager.verify_edit_password(old_pwd):
                QMessageBox.warning(self, "错误", "原密码错误，无法修改。")
                return
        # 请求新密码
        new_pwd, ok = QInputDialog.getText(self, "设置编辑密码", 
                                       "请输入新密码（留空以清除）:", 
                                       QLineEdit.Password)
        if ok:
            #self.manager = ShipManager("config.json")
            self.manager.set_edit_password(new_pwd)
            if new_pwd:
                QMessageBox.information(self, "完成", "编辑密码已设置。")
            else:
                QMessageBox.information(self, "完成", "编辑密码已清除。")

    def open_settings(self):
        if self.main_window:
            self.main_window.open_settings()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", "无法打开设置页面。")

    def batch_set_owned_true(self):
        self.batch_operation_signal.emit("owned_true", self.get_criteria())

    def batch_set_owned_false(self):
        self.batch_operation_signal.emit("owned_false", self.get_criteria())

    def batch_set_oath_true(self):
        self.batch_operation_signal.emit("oath_true", self.get_criteria())

    def batch_set_oath_false(self):
        self.batch_operation_signal.emit("oath_false", self.get_criteria())

    def batch_set_max_true(self):
        self.batch_operation_signal.emit("max_true", self.get_criteria())

    def batch_set_max_false(self):
        self.batch_operation_signal.emit("max_false", self.get_criteria())

    def batch_set_120_true(self):
        self.batch_operation_signal.emit("120_true", self.get_criteria())

    def batch_set_120_false(self):
        self.batch_operation_signal.emit("120_false", self.get_criteria())

    def batch_set_remodeled_true(self):
        self.batch_operation_signal.emit("remodeled_true", self.get_criteria())

    def batch_set_remodeled_false(self):
        self.batch_operation_signal.emit("remodeled_false", self.get_criteria())