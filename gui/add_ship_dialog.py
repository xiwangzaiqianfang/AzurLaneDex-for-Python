from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QComboBox, QCheckBox, QDialogButtonBox, QTextEdit,
                               QGroupBox, QGridLayout, QSpinBox, QScrollArea,
                               QLabel, QWidget, QHBoxLayout, QPushButton, QAbstractSpinBox,
                               QDateEdit, QFrame, QMessageBox, QButtonGroup, QRadioButton)
from PySide6.QtCore import Qt, QDate
from models import Ship

class AddShipDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增舰船")
        self.resize(800, 700)
        main_layout = QVBoxLayout(self)
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        # 滚动区域的内容容器
        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10) 
        content_layout.setContentsMargins(10, 10, 10, 10)
        # 定义公共卡片样式（可在样式表中统一，这里先设置objectName）
        self.card_template = lambda title: (lambda card: (
            card.setObjectName("card"),
            card_layout := QVBoxLayout(card),
            card_layout.setContentsMargins(10, 10, 10, 10),
            title_label := QLabel(title),
            title_label.setObjectName("cardTitle"),
            card_layout.addWidget(title_label),
            (card, card_layout)  # 返回卡片和布局
        ))
        # ---- 基本信息区域 ----
        basic_card = QFrame()
        basic_card.setObjectName("card")
        basic_layout = QVBoxLayout(basic_card)
        basic_layout.setContentsMargins(10, 10, 10, 10)

        basic_title = QLabel("基本信息")
        basic_title.setObjectName("cardTitle")
        basic_layout.addWidget(basic_title)

        basic_form = QFormLayout()
        basic_form.setContentsMargins(0, 0, 0, 0)
        #basic_group = QGroupBox("基本信息")
        #basic_form = QFormLayout(basic_group)
        id_layout = QHBoxLayout()
        self.id_spin = QSpinBox()
        self.id_spin.setRange(0, 9999)       # 允许范围，0 表示自动分配
        self.id_spin.setSpecialValueText("自动")  # 显示“自动”表示自动分配
        self.id_spin.setValue(0)              # 默认自动
        self.id_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.id_spin.setFixedWidth(80)
        id_minus = QPushButton("-")
        id_plus = QPushButton("+")
        id_minus.setFixedSize(35, 30)
        id_plus.setFixedSize(35, 30)
        id_minus.clicked.connect(lambda: self.id_spin.setValue(self.id_spin.value() - 1))
        id_plus.clicked.connect(lambda: self.id_spin.setValue(self.id_spin.value() + 1))
        id_layout.addWidget(self.id_spin)
        id_layout.addWidget(id_minus)
        id_layout.addWidget(id_plus)
        basic_form.addRow("编号:", id_layout)

        order_layout = QHBoxLayout()
        self.game_order_spin = QSpinBox()
        self.game_order_spin.setRange(0, 9999)
        self.game_order_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.game_order_spin.setFixedWidth(80)
        order_minus = QPushButton("-")
        order_plus = QPushButton("+")
        order_minus.setFixedSize(35, 30)
        order_plus.setFixedSize(35, 30)
        order_minus.clicked.connect(lambda: self.game_order_spin.setValue(self.game_order_spin.value() - 1))
        order_plus.clicked.connect(lambda: self.game_order_spin.setValue(self.game_order_spin.value() + 1))
        order_layout.addWidget(self.game_order_spin)
        order_layout.addWidget(order_minus)
        order_layout.addWidget(order_plus)
        basic_form.addRow("游戏内图鉴顺序 (0=自动):", order_layout)

        self.name_edit = QLineEdit()
        self.alt_name_edit = QLineEdit()
        self.faction_combo = QComboBox()
        self.faction_combo.addItems(["请选择", "白鹰", "皇家", "重樱", "铁血", "东煌", "撒丁帝国", "北方联合", "自由鸢尾", "维希教廷", "郁金王国", "飓风", "META", "其他"])
        self.class_combo = QComboBox()
        self.class_combo.addItems(["请选择","驱逐", "轻巡", "重巡", "超巡", "战巡", "战列", "航母", "轻航", "航战", "重炮", "维修", "潜艇", "潜母", "运输", "风帆"])
        self.class_combo.currentTextChanged.connect(self.update_default_affects)
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItems(["请选择","普通", "稀有", "精锐", "超稀有", "海上传奇", "最高方案", "决战方案"])
        
        self.can_remodel_cb = QCheckBox("可改造")
        self.remodel_date_edit = QDateEdit()
        self.remodel_date_edit.setCalendarPopup(True)
        self.remodel_date_edit.setDate(QDate.currentDate())
        self.remodel_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.remodel_date_edit.setEnabled(False)
        self.can_remodel_cb.toggled.connect(self.remodel_date_edit.setEnabled)

        self.acquire_main_edit = QLineEdit()
        self.acquire_detail_edit = QLineEdit()
        self.build_time_edit = QLineEdit()
        self.drop_locations_edit = QLineEdit()
        self.shop_exchange_edit = QLineEdit()
        self.is_permanent_cb = QCheckBox("常驻")
        self.is_permanent_cb.setChecked(True)
        self.debut_event_edit = QLineEdit()
        self.release_date_edit = QDateEdit()
        self.release_date_edit.setCalendarPopup(True)
        self.release_date_edit.setDate(QDate.currentDate())
        self.release_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.notes_edit = QLineEdit()
        self.notes_edit.setMaximumHeight(80)
        
        self.can_special_gear_cb = QCheckBox("可拥有特殊兵装")
        self.special_gear_name_edit = QLineEdit()
        self.special_gear_name_edit.setEnabled(False)
        self.special_gear_date_edit = QDateEdit()
        self.special_gear_date_edit.setCalendarPopup(True)
        self.special_gear_date_edit.setDate(QDate.currentDate())
        self.special_gear_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.special_gear_date_edit.setEnabled(False)
        self.special_gear_acquire_edit = QLineEdit()
        self.special_gear_acquire_edit.setEnabled(False)
        self.can_special_gear_cb.toggled.connect(self.toggle_special_gear)

        self.image_path_edit = QLineEdit()

        basic_form.addRow("名称:", self.name_edit)
        basic_form.addRow("和谐名称:", self.alt_name_edit)
        basic_form.addRow("阵营:", self.faction_combo)
        basic_form.addRow("舰种:", self.class_combo)
        basic_form.addRow("稀有度:", self.rarity_combo)
        basic_form.addRow("", self.can_remodel_cb)
        basic_form.addRow("改造日期:", self.remodel_date_edit)
        basic_form.addRow("主要获取方式:", self.acquire_main_edit)
        basic_form.addRow("详细信息:", self.acquire_detail_edit)
        basic_form.addRow("建造时间:", self.build_time_edit)
        basic_form.addRow("打捞地点(分号分隔):", self.drop_locations_edit)
        basic_form.addRow("商店兑换:", self.shop_exchange_edit)
        basic_form.addRow("", self.is_permanent_cb)
        basic_form.addRow("首次登场活动:", self.debut_event_edit)
        basic_form.addRow("实装时间:", self.release_date_edit)
        basic_form.addRow("备注:", self.notes_edit)

        # 特殊兵装组（可折叠/启用）
        basic_form.addRow("", self.can_special_gear_cb)
        basic_form.addRow("特殊兵装名称:", self.special_gear_name_edit)
        basic_form.addRow("实装日期:", self.special_gear_date_edit)
        basic_form.addRow("获取途径:", self.special_gear_acquire_edit)
        basic_form.addRow("立绘地址:", self.image_path_edit)

        #content_layout.addWidget(basic_group)
        basic_layout.addLayout(basic_form)
        content_layout.addWidget(basic_card)

        # ---- 属性加成（获得/120级） ----
        attr_card = QFrame()
        attr_card.setObjectName("card")
        attr_layout = QVBoxLayout(attr_card)
        attr_layout.setContentsMargins(10, 10, 10, 10)

        attr_title = QLabel("属性加成 (获得/120级)")
        attr_title.setObjectName("cardTitle")
        attr_layout.addWidget(attr_title)
        self.attr_spins = {}

        # 获得时加成组
        obtain_group = QGroupBox("获得时加成")
        obtain_layout = QVBoxLayout(obtain_group)

        # 数值行
        obtain_value_layout = QHBoxLayout()
        obtain_value_layout.addWidget(QLabel("数值:"))
        self.obtain_value_spin = QSpinBox()
        self.obtain_value_spin.setRange(0, 999)
        self.obtain_value_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # 加减按钮
        obtain_minus = QPushButton("-")
        obtain_plus = QPushButton("+")
        obtain_minus.clicked.connect(lambda: self.obtain_value_spin.setValue(self.obtain_value_spin.value() - 1))
        obtain_plus.clicked.connect(lambda: self.obtain_value_spin.setValue(self.obtain_value_spin.value() + 1))
        obtain_value_layout.addWidget(self.obtain_value_spin)
        obtain_value_layout.addWidget(obtain_minus)
        obtain_value_layout.addWidget(obtain_plus)
        obtain_value_layout.addStretch()
        obtain_layout.addLayout(obtain_value_layout)

        # 属性选择（单选）
        obtain_attr_label = QLabel("加成属性:")
        obtain_layout.addWidget(obtain_attr_label)
        self.obtain_attr_group = QButtonGroup(self)
        obtain_attrs_layout = QHBoxLayout()
        attr_list = ["耐久", "炮击", "雷击", "防空", "航空", "命中", "装填", "机动", "反潜"]
        self.tech_items = [
            ("耐久", "durability"),
            ("炮击", "firepower"),
            ("雷击", "torpedo"),
            ("防空", "aa"),
            ("航空", "aviation"),
            ("命中", "accuracy"),
            ("装填", "reload"),
            ("机动", "mobility"),
            ("反潜", "antisub")
        ]
        self.obtain_attr_radios = {}
        for attr in attr_list:
            rb = QRadioButton(attr)
            self.obtain_attr_group.addButton(rb)
            self.obtain_attr_radios[attr] = rb
            obtain_attrs_layout.addWidget(rb)
        obtain_attrs_layout.addStretch()
        obtain_layout.addLayout(obtain_attrs_layout)

        # 适用舰种（多选，网格布局，一行3~4个）
        obtain_shipclass_label = QLabel("适用舰种:")
        obtain_layout.addWidget(obtain_shipclass_label)
        self.obtain_affect_grid = QGridLayout()
        self.obtain_affect_checkboxes = {}
        ship_classes = ["驱逐", "轻巡", "重巡", "超巡", "战巡", "战列", "航母", "轻航", "航战", "重炮", "维修", "潜艇", "潜母", "运输", "风帆"]
        columns = 4
        for idx, sc in enumerate(ship_classes):
            cb = QCheckBox(sc)
            row = idx // columns
            col = idx % columns
            self.obtain_affect_grid.addWidget(cb, row, col)
            self.obtain_affect_checkboxes[sc] = cb
        obtain_layout.addLayout(self.obtain_affect_grid)

        attr_layout.addWidget(obtain_group)

        # 创建 level120 组
        level120_group = QGroupBox("120级时加成")
        level120_layout = QVBoxLayout(level120_group)

        # 数值行
        level120_value_layout = QHBoxLayout()
        level120_value_layout.addWidget(QLabel("数值:"))
        self.level120_value_spin = QSpinBox()
        self.level120_value_spin.setRange(0, 999)
        self.level120_value_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        level120_minus = QPushButton("-")
        level120_plus = QPushButton("+")
        level120_minus.clicked.connect(lambda: self.level120_value_spin.setValue(self.level120_value_spin.value() - 1))
        level120_plus.clicked.connect(lambda: self.level120_value_spin.setValue(self.level120_value_spin.value() + 1))
        level120_value_layout.addWidget(self.level120_value_spin)
        level120_value_layout.addWidget(level120_minus)
        level120_value_layout.addWidget(level120_plus)
        level120_value_layout.addStretch()
        level120_layout.addLayout(level120_value_layout)

        # 属性选择
        level120_attr_label = QLabel("加成属性:")
        level120_layout.addWidget(level120_attr_label)
        self.level120_attr_group = QButtonGroup(self)
        self.level120_attr_radios = {}
        level120_attrs_layout = QHBoxLayout()
        for attr in attr_list:
            rb = QRadioButton(attr)
            self.level120_attr_group.addButton(rb)
            self.level120_attr_radios[attr] = rb
            level120_attrs_layout.addWidget(rb)
        level120_attrs_layout.addStretch()
        level120_layout.addLayout(level120_attrs_layout)

        # 适用舰种
        level120_shipclass_label = QLabel("适用舰种:")
        level120_layout.addWidget(level120_shipclass_label)
        self.level120_affect_grid = QGridLayout()
        self.level120_affect_checkboxes = {}
        for idx, sc in enumerate(ship_classes):
            cb = QCheckBox(sc)
            row = idx // columns
            col = idx % columns
            self.level120_affect_grid.addWidget(cb, row, col)
            self.level120_affect_checkboxes[sc] = cb
        level120_layout.addLayout(self.level120_affect_grid)
        attr_layout.addWidget(level120_group)
        
        content_layout.addWidget(attr_card)
        #content_layout.addWidget(attr_group)

        # ---- 科技点总和（三阶段） ----
        points_card = QFrame()
        points_card.setObjectName("card")
        points_layout = QVBoxLayout(points_card)
        points_layout.setContentsMargins(10, 10, 10, 10)

        points_title = QLabel("科技点总和")
        points_title.setObjectName("cardTitle")
        points_layout.addWidget(points_title)
        #points_group = QGroupBox("科技点总和")
        #points_layout = QFormLayout(points_group)

        form_points = QFormLayout()
        form_points.setContentsMargins(0, 0, 0, 0)

        # 获得
        obtain_container, self.tech_points_obtain = self.create_spin_with_buttons(min_val=0, max_val=100, suffix=" 点")
        #points_layout.addRow("获得:", obtain_container)

        # 满破
        max_container, self.tech_points_max = self.create_spin_with_buttons(min_val=0, max_val=100, suffix=" 点")
        #points_layout.addRow("满破:", max_container)

        # 120级
        level120_container, self.tech_points_120 = self.create_spin_with_buttons(min_val=0, max_val=100, suffix=" 点")
        #points_layout.addRow("120级:", level120_container)
        form_points.addRow("获得:", obtain_container)
        form_points.addRow("满破:", max_container)
        form_points.addRow("120级:", level120_container)

        points_layout.addLayout(form_points)
        content_layout.addWidget(points_card)
        #content_layout.addWidget(points_group)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        content_layout.addWidget(button_box)

    def create_spin_with_buttons(self, min_val=0, max_val=100, suffix="", fixed_width=90):
        """创建一个带加减按钮的SpinBox容器"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSuffix(suffix)
        spin.setButtonSymbols(QAbstractSpinBox.NoButtons)  # 隐藏自带箭头
        spin.setAlignment(Qt.AlignRight)
        spin.setFixedWidth(fixed_width)  # 固定宽度，可根据需要调整

        minus_btn = QPushButton("-")
        plus_btn = QPushButton("+")
        minus_btn.setFixedSize(35, 30)
        plus_btn.setFixedSize(35, 30)

        # 连接按钮
        minus_btn.clicked.connect(lambda: spin.setValue(spin.value() - 1))
        plus_btn.clicked.connect(lambda: spin.setValue(spin.value() + 1))

        layout.addWidget(spin)
        layout.addWidget(minus_btn)
        layout.addWidget(plus_btn)

        return container, spin  # 返回容器和spin以便后续获取值
    
    def toggle_special_gear(self):
        enabled = self.can_special_gear_cb.isChecked()
        #print(f"特殊兵装选项 {'启用' if enabled else '禁用'}")
        self.special_gear_name_edit.setEnabled(enabled)
        self.special_gear_date_edit.setEnabled(enabled)
        self.special_gear_acquire_edit.setEnabled(enabled)

    def update_default_affects(self, ship_class):
        # 先清除两组复选框的所有勾选
        for cb in self.obtain_affect_checkboxes.values():
            cb.setChecked(False)
        for cb in self.level120_affect_checkboxes.values():
            cb.setChecked(False)

        # 根据舰种设置默认勾选
        default_map = {
            "驱逐": {
                "obtain": ["驱逐"],
                "level120": ["驱逐"]
            },
            "轻巡": {
                "obtain": ["轻巡"],
                "level120": ["轻巡"]
            },
            "重巡":  {
                "obtain": ["重巡", "超巡", "重炮"],
                "level120": ["重巡", "超巡", "重炮"]
            },
            "超巡": {
                "obtain": ["重巡", "超巡", "重炮"],
                "level120": ["重巡", "超巡", "重炮"]
            },
            "重炮": {
                "obtain": ["重巡", "超巡", "重炮"],
                "level120": ["重巡", "超巡", "重炮"]
            },
            "战巡": {
                "obtain": ["战巡", "战列", "航战"],
                "level120": ["战巡"]
            },
            "战列": {
                "obtain": ["战巡", "战列", "航战"],
                "level120": ["战巡", "战列", "航战"]
            },
            "航战": {
                "obtain": ["战巡", "战列", "航战"],
                "level120": ["航战"]
            },
            "航母": {
                "obtain": ["航母", "轻航"],
                "level120": ["航母"]
            },
            "轻航": {
                "obtain": ["轻航"],
                "level120": ["航母", "轻航"]
            },
            "维修": {
                "obtain": ["维修"],
                "level120": ["维修"]
            },
            "潜艇": {
                "obtain": ["潜艇", "潜母"],
                "level120": ["潜艇", "潜母"]
            },
            "潜母": {
                "obtain": ["潜艇", "潜母"],
                "level120": ["潜艇", "潜母"]
            },
            "运输": {
                "obtain": ["运输"],
                "level120": ["运输"]
            },
            "风帆": {
                "obtain": ["风帆"],
                "level120": ["风帆"]
            },
        }

        if ship_class in default_map:
            obtain_preset = default_map[ship_class]["obtain"]
            level120_preset = default_map[ship_class]["level120"]
        else:
            obtain_preset = [ship_class] if ship_class in self.obtain_affect_checkboxes else []
            level120_preset = [ship_class] if ship_class in self.level120_affect_checkboxes else []

        # 设置获得时适用舰种
        for sc in obtain_preset:
            if sc in self.obtain_affect_checkboxes:
                self.obtain_affect_checkboxes[sc].setChecked(True)

        # 设置120级适用舰种
        for sc in level120_preset:
            if sc in self.level120_affect_checkboxes:
                self.level120_affect_checkboxes[sc].setChecked(True)

    def validate_and_accept(self):
        """验证输入，通过则关闭对话框，否则不关闭并提示"""
        if self.faction_combo.currentText() == "请选择" or \
            self.class_combo.currentText() == "请选择" or \
            self.rarity_combo.currentText() == "请选择":
            QMessageBox.warning(self, "输入不完整", "请完整选择阵营、舰种和稀有度。")
            return  # 不关闭对话框
        # 可以在此添加其他必要字段的验证（如名称不能为空等）
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "输入不完整", "请输入舰船名称。")
            return
        # 所有验证通过，关闭对话框
        self.accept()

    def get_ship(self):
        # 校验必选字段
        #if self.faction_combo.currentText() == "请选择" or \
        #    self.class_combo.currentText() == "请选择" or \
        #    self.rarity_combo.currentText() == "请选择":
        #    from PySide6.QtWidgets import QMessageBox
        #    QMessageBox.warning(self, "输入不完整", "请完整选择阵营、舰种和稀有度。")
        #    return None  # 返回 None 表示取消添加
        manual_id = self.id_spin.value()
        ship_id = 0 if manual_id == 0 else manual_id
        game_order = self.game_order_spin.value()
        can_remodel = self.can_remodel_cb.isChecked()
        remodel_date = self.remodel_date_edit.date().toString("yyyy-MM-dd") if can_remodel else ""
        if self.can_special_gear_cb.isChecked():
            special_gear_name = self.special_gear_name_edit.text()
            special_gear_date = self.special_gear_date_edit.date().toString("yyyy-MM-dd")
            special_gear_acquire = self.special_gear_acquire_edit.text()
        else:
            special_gear_name = special_gear_date = special_gear_acquire = ""

        # 获取获得时加成
        obtain_bonus_attr = ""
        for attr, rb in self.obtain_attr_radios.items():
            if rb.isChecked():
                obtain_bonus_attr = attr
                break
        obtain_bonus_value = self.obtain_value_spin.value()
        obtain_affects = [sc for sc, cb in self.obtain_affect_checkboxes.items() if cb.isChecked()]
        
        # 获取120级时加成
        level120_bonus_attr = ""
        for attr, rb in self.level120_attr_radios.items():
            if rb.isChecked():
                level120_bonus_attr = attr
                break
        level120_bonus_value = self.level120_value_spin.value()
        level120_affects = [sc for sc, cb in self.level120_affect_checkboxes.items() if cb.isChecked()]
        
        # 科技点总和
        tech_points_obtain = self.tech_points_obtain.value()
        tech_points_max = self.tech_points_max.value()
        tech_points_120 = self.tech_points_120.value()
        
        # 构建 Ship 参数字典
        ship_kwargs = {
            "id": ship_id,
            "game_order": game_order,
            "name": self.name_edit.text(),
            "alt_name": self.alt_name_edit.text().strip(),
            "faction": self.faction_combo.currentText(),
            "ship_class": self.class_combo.currentText(),
            "rarity": self.rarity_combo.currentText(),
            "owned": False,
            "breakthrough": 0,
            "can_remodel": can_remodel,
            "remodel_date": remodel_date,
            "remodeled": False,
            "oath": False,
            "level_120": False,
            "acquire_main": self.acquire_main_edit.text(),
            "acquire_detail": self.acquire_detail_edit.text(),
            "build_time": self.build_time_edit.text(),
            "drop_locations": [s.strip() for s in self.drop_locations_edit.text().split(';') if s.strip()],
            "shop_exchange": self.shop_exchange_edit.text(),
            "is_permanent": self.is_permanent_cb.isChecked(),
            "debut_event": self.debut_event_edit.text(),
            "release_date": self.release_date_edit.date().toString("yyyy-MM-dd"),
            "notes": self.notes_edit.text(),
            "image_path": self.image_path_edit.text(),
            "tech_affects": [],   # 已废弃
            "tech_points_obtain": tech_points_obtain,
            "tech_points_max": tech_points_max,
            "tech_points_120": tech_points_120,
            "obtain_bonus_attr": obtain_bonus_attr,
            "obtain_bonus_value": obtain_bonus_value,
            "obtain_affects": obtain_affects,
            "level120_bonus_attr": level120_bonus_attr,
            "level120_bonus_value": level120_bonus_value,
            "level120_affects": level120_affects,
            "can_special_gear": self.can_special_gear_cb.isChecked(),
            "special_gear_name": special_gear_name,
            "special_gear_date": special_gear_date,
            "special_gear_acquire": special_gear_acquire,
            "special_gear_obtained": False,
        }

        ship = Ship(**ship_kwargs)
        print(f"新建舰船: id={ship.id}, name={ship.name}")
        print("新建船字典:", ship.to_dict())
        return ship