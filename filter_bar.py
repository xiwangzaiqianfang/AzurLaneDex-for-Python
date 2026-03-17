from PySide6.QtWidgets import (QWidget, QHBoxLayout, QComboBox, QCheckBox, QPushButton, QLabel, QLineEdit, QToolButton, QMenu, QStyle, QCompleter)
from PySide6.QtCore import Signal, QStringListModel
from PySide6.QtGui import QAction, QIcon, QFont, QFontDatabase, Qt
import os
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

    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 常用按钮
        row1 = QHBoxLayout()
        row1.setSpacing(5)
        # 阵营
        row1.addWidget(QLabel("阵营:"))
        self.faction_combo = QComboBox()
        self.faction_combo.addItems(["全部", "白鹰", "皇家", "重樱", "铁血", "东煌", "撒丁", "北方联合", "鸢尾", "维希教廷", "META", "其他"])
        self.faction_combo.currentTextChanged.connect(self.on_filter_changed)
        row1.addWidget(self.faction_combo)

        # 舰种
        row1.addWidget(QLabel("舰种:"))
        self.class_combo = QComboBox()
        self.class_combo.addItems(["全部", "驱逐", "轻巡", "重巡", "超巡", "战巡", "战列", "航母", "轻航", "航战", "重炮", "维修", "潜艇", "潜母", "其他"])
        self.class_combo.currentTextChanged.connect(self.on_filter_changed)
        row1.addWidget(self.class_combo)

        # 稀有度
        row1.addWidget(QLabel("稀有度:"))
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItems(["全部", "普通", "稀有", "精锐", "超稀有", "海上传奇"])
        self.rarity_combo.currentTextChanged.connect(self.on_filter_changed)
        row1.addWidget(self.rarity_combo)

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

        self.stat_btn = QPushButton("一键统计")
        self.stat_btn.clicked.connect(self.stat_clicked)
        row1.addWidget(self.stat_btn)

        self.fleet_tech_btn = QPushButton("舰队科技")
        self.fleet_tech_btn.clicked.connect(self.fleet_tech_clicked.emit)
        row1.addWidget(self.fleet_tech_btn)

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

        action_update = QAction("网络更新", self)
        action_update.triggered.connect(self.update_online_clicked.emit)
        menu.addAction(action_update)

        action_theme = QAction("切换主题", self)
        action_theme.triggered.connect(self.theme_toggled.emit)
        menu.addAction(action_theme)

        row1.addWidget(self.more_btn)

        row1.addStretch()
        main_layout.addLayout(row1)

        self.adv_panel = None

        # 高级筛选选项（初始隐藏）
        #self.adv_widget = QWidget()
        #adv_layout = QHBoxLayout(self.adv_widget)
        #adv_layout.setContentsMargins(0, 0, 0, 0)

        # 复选框
        #self.owned_cb = QCheckBox("已获得")
        #self.owned_cb.stateChanged.connect(self.on_filter_changed)
        #self.not_owned_cb = QCheckBox("未获得")
        #row1.addWidget(self.oath_cb)

        #self.remodel_cb = QCheckBox("可改造")
        #self.remodel_cb.stateChanged.connect(self.on_filter_changed)
        #row1.addWidget(self.remodel_cb)

        #self.remodeled_cb = QCheckBox("已改造")
        #self.remodeled_cb.stateChanged.connect(self.on_filter_changed)
        #row1.addWidget(self.remodeled_cb)
        #self.can_remodel_not_cb = QCheckBox("未改造")

        #self.oath_cb = QCheckBox("已誓约")
        #self.oath_cb.stateChanged.connect(self.on_filter_changed)
        #row1.addWidget(self.oath_cb)

        #self.max_cb = QCheckBox("已满破")
        #self.max_cb.stateChanged.connect(self.on_filter_changed)
        #row1.addWidget(self.max_cb)
        #self.not_max_cb = QCheckBox("未满破")

        #self.level120_cb = QCheckBox("120级")
        #self.level120_cb.stateChanged.connect(self.on_filter_changed)
        #self.not_level120_cb = QCheckBox("未120级")
        #row1.addWidget(self.level120_cb)

        #for cb in [self.not_owned_cb, self.not_max_cb, self.not_level120_cb, self.can_remodel_not_cb]:
        #    cb.stateChanged.connect(self.on_filter_changed)
        #    adv_layout.addWidget(cb)
        #adv_layout.addStretch()
        #self.adv_widget.setVisible(False)  # 初始隐藏
        #main_layout.addWidget(self.adv_widget)

        # 加载自定义字体
        #font_path = os.path.join(os.path.dirname(__file__), "..", "fonts", "Segoe Fluent Icons.ttf")
        #print("尝试加载字体:", os.path.abspath(font_path))  # 添加调试打印
        #font_id = QFontDatabase.addApplicationFont(font_path)
        #print("搜索icon字体ID:", font_id)
        #if font_id != -1:
        #    font_families = QFontDatabase.applicationFontFamilies(font_id)
        #    print("字体族:", font_families)
        #    if font_families:
        #        icon_font_family = font_families[0]
        #    else:
        #        icon_font_family = "Segoe MDL2 Assets"  # 回退
        #else:
        #    icon_font_family = "Segoe MDL2 Assets"  # 加载失败时回退
        

        #print("复选框互斥状态：")
        #for cb in [self.remodel_cb, self.oath_cb, self.owned_cb, self.max_cb, self.level120_cb]:
        # print(f"{cb.text()}: autoExclusive={cb.autoExclusive()}")

    #def toggle_advanced(self, checked):
    #    """展开/收起高级筛选"""
    #    self.adv_widget.setVisible(checked)
    #    self.adv_btn.setText("高级筛选 ▲" if checked else "高级筛选 ▼")

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
        #if self.remodel_cb.isChecked():
        #    criteria['can_remodel'] = True
        #if self.oath_cb.isChecked():
        #    criteria['oath'] = True
        #if self.owned_cb.isChecked():
        #    criteria['owned'] = True
        #if self.max_cb.isChecked():
        #    criteria['max_breakthrough'] = True
        #if self.level120_cb.isChecked():
        #    criteria['level_120'] = True
        self.filter_changed.emit(criteria)

    def reset(self):
        self.faction_combo.setCurrentText("全部")
        self.class_combo.setCurrentText("全部")
        self.rarity_combo.setCurrentText("全部")
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
        #if self.remodel_cb.isChecked():
        #    criteria['can_remodel'] = True
        #if self.remodeled_cb.isChecked():
        #    criteria['remodeled'] = True
        #if self.oath_cb.isChecked():
        #    criteria['oath'] = True
        #if self.owned_cb.isChecked():
        #    criteria['owned'] = True
        #if self.max_cb.isChecked():
        #    criteria['max_breakthrough'] = True
        #if self.level120_cb.isChecked():
        #    criteria['level_120'] = True
        #if self.not_owned_cb.isChecked():
        #    criteria['not_owned'] = True
        #if self.not_max_cb.isChecked():
        #    criteria['not_max'] = True
        #if self.not_level120_cb.isChecked():
        #    criteria['not_level120'] = True
        #if self.can_remodel_not_cb.isChecked():
        #    criteria['can_remodel_not'] = True
        #print("基础条件返回:", criteria)
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

    #def on_more_menu_shown(self):
    #    self.more_btn.setText(self.base_text + " ")

    #def on_more_menu_hidden(self):
    #    self.more_btn.setText(self.base_text + " ")