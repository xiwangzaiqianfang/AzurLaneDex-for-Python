from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QComboBox, QCheckBox, QDialogButtonBox, QTextEdit, QGroupBox, QGridLayout, QSpinBox, QScrollArea,
                               QLabel, QWidget, QHBoxLayout, QPushButton, QAbstractSpinBox, QDateEdit, QFrame, QMessageBox)
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
        basic_form.addRow("编号 (0=自动):", id_layout)

        self.name_edit = QLineEdit()
        self.faction_combo = QComboBox()
        self.faction_combo.addItems(["请选择", "白鹰", "皇家", "重樱", "铁血", "东煌", "撒丁帝国", "北方联合", "自由鸢尾", "维希教廷", "郁金王国", "飓风", "META", "其他"])
        self.class_combo = QComboBox()
        self.class_combo.addItems(["请选择","驱逐", "轻巡", "重巡", "超巡", "战巡", "战列", "航母", "轻航", "航战", "重炮", "维修", "潜艇", "潜母", "运输", "风帆"])
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItems(["请选择","普通", "稀有", "精锐", "超稀有", "海上传奇", "最高方案", "决战方案"])
        self.can_remodel_cb = QCheckBox("可改造")
        # 改造日期控件（默认禁用）
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
        #self.release_date_edit = QLineEdit()
        self.release_date_edit = QDateEdit()
        self.release_date_edit.setCalendarPopup(True)
        self.release_date_edit.setDate(QDate.currentDate())
        self.release_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.notes_edit = QLineEdit()
        self.notes_edit.setMaximumHeight(80)
        self.image_path_edit = QLineEdit()

        basic_form.addRow("名称:", self.name_edit)
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
        #attr_group = QGroupBox("属性加成 (获得/120级)")
        #attr_layout = QGridLayout(attr_group)

        # 表头
        #attr_layout.addWidget(QLabel("属性"), 0, 0)
        #attr_layout.addWidget(QLabel("获得"), 0, 1)
        #attr_layout.addWidget(QLabel("120级"), 0, 2)

        #attr_layout.setHorizontalSpacing(2)   # 设置列间距为2
        #attr_layout.setVerticalSpacing(5)     # 可选，调整行间距
        # 使用网格布局放置控件
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(5)
        grid.addWidget(QLabel("属性"), 0, 0)
        grid.addWidget(QLabel("获得"), 0, 1)
        grid.addWidget(QLabel("120级"), 0, 2)

        # 定义科技项（已在 __init__ 中定义为 self.tech_items，但确保可用）
        if not hasattr(self, 'tech_items'):
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

        self.attr_spins = {}
        for row, (label, base) in enumerate(self.tech_items, start=1):
            #attr_layout.addWidget(QLabel(label), row, 0)
            grid.addWidget(QLabel(label), row, 0)
            for col, suffix in enumerate(["obtain", "120"], start=1):
                container, spin = self.create_spin_with_buttons(min_val=0, max_val=999)
                grid.addWidget(container, row, col)
                self.attr_spins[f"tech_{base}_{suffix}"] = spin
           # 获得阶段
            #container_obtain, spin_obtain = self.create_spin_with_buttons(min_val=0, max_val=999)
            #attr_layout.addWidget(container_obtain, row, 1)
            #self.attr_spins[f"tech_{base}_obtain"] = spin_obtain
            # 120级阶段
            #container_120, spin_120 = self.create_spin_with_buttons(min_val=0, max_val=999)
            #attr_layout.addWidget(container_120, row, 2)
            #self.attr_spins[f"tech_{base}_120"] = spin_120

        attr_layout.addLayout(grid)
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
        obtain_container, self.tech_points_obtain = self.create_spin_with_buttons(min_val=0, max_val=50, suffix=" 点")
        #points_layout.addRow("获得:", obtain_container)

        # 满破
        max_container, self.tech_points_max = self.create_spin_with_buttons(min_val=0, max_val=50, suffix=" 点")
        #points_layout.addRow("满破:", max_container)

        # 120级
        level120_container, self.tech_points_120 = self.create_spin_with_buttons(min_val=0, max_val=50, suffix=" 点")
        #points_layout.addRow("120级:", level120_container)
        form_points.addRow("获得:", obtain_container)
        form_points.addRow("满破:", max_container)
        form_points.addRow("120级:", level120_container)

        points_layout.addLayout(form_points)
        content_layout.addWidget(points_card)
        #content_layout.addWidget(points_group)

        # ---- 科技点适用舰种组 ----
        affect_card = QFrame()
        affect_card.setObjectName("card")
        affect_layout = QVBoxLayout(affect_card)
        affect_layout.setContentsMargins(10, 10, 10, 10)

        affect_title = QLabel("科技点适用舰种（一般使用系统自动分配项即可）")
        affect_title.setObjectName("cardTitle")
        affect_layout.addWidget(affect_title)
        #affect_group = QGroupBox("科技点适用舰种（一般使用系统自动分配项即可）")
        #affect_layout = QGridLayout(affect_group)

        # 所有舰种列表
        ship_classes = ["驱逐", "轻巡", "重巡", "超巡", "战巡", "战列", "航母", "轻航", "航战", "重炮", "维修", "潜艇", "潜母", "运输", "风帆"]
        self.affect_checkboxes = {}
        grid_affect = QGridLayout()
        grid_affect.setHorizontalSpacing(15)
        grid_affect.setVerticalSpacing(5)
        columns = 3
        for index, sc in enumerate(ship_classes):
            cb = QCheckBox(sc)
            row = index // columns
            col = index % columns
            #affect_layout.addWidget(cb, row, col)
            grid_affect.addWidget(cb, row, col)
            self.affect_checkboxes[sc] = cb

        # 将组放入滚动区域（防止内容过多）
        #affect_scroll = QScrollArea()
        #affect_scroll.setWidgetResizable(True)
        #affect_scroll.setWidget(affect_group)
        #content_layout.addWidget(affect_scroll)  # content_layout 是对话框的主布局
        
        self.class_combo.currentTextChanged.connect(self.update_default_affects)
        #content_layout.addWidget(affect_group)

        affect_layout.addLayout(grid_affect)
        content_layout.addWidget(affect_card)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        content_layout.addWidget(button_box)

    def create_spin_with_buttons(self, min_val=0, max_val=100, suffix="", fixed_width=65):
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

    def update_default_affects(self, ship_class):
        # 先全部取消勾选
        for cb in self.affect_checkboxes.values():
           cb.setChecked(False)

        # 根据舰种设置默认勾选
        if ship_class == "驱逐":
            self.affect_checkboxes["驱逐"].setChecked(True)
        elif ship_class == "轻巡":
            self.affect_checkboxes["轻巡"].setChecked(True)
        elif ship_class in ["重巡", "重炮", "超巡"]:
            for c in ["重巡", "重炮", "超巡"]:
                if c in self.affect_checkboxes:
                    self.affect_checkboxes[c].setChecked(True)
        elif ship_class in ["战巡", "战列", "航战"]:
            for c in ["战巡", "战列", "航战"]:
                if c in self.affect_checkboxes:
                    self.affect_checkboxes[c].setChecked(True)
        elif ship_class == "轻航":
            self.affect_checkboxes["轻航"].setChecked(True)
        elif ship_class == "航母":
            if "轻航" in self.affect_checkboxes:
                self.affect_checkboxes["轻航"].setChecked(True)
            if "航母" in self.affect_checkboxes:
                self.affect_checkboxes["航母"].setChecked(True)
        elif ship_class in ["潜艇", "潜母"]:
            for c in ["潜艇", "潜母"]:
                if c in self.affect_checkboxes:
                    self.affect_checkboxes[c].setChecked(True)
        elif ship_class == "运输":
            self.affect_checkboxes["运输"].setChecked(True)
        elif ship_class == "风帆":
            self.affect_checkboxes["风帆"].setChecked(True)
        elif ship_class == "维修":
            self.affect_checkboxes["维修"].setChecked(True)
        else:
            # 默认只勾选自身
            if ship_class in self.affect_checkboxes:
                self.affect_checkboxes[ship_class].setChecked(True)

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
        if self.can_remodel_cb.isChecked():
            remodel_date = self.remodel_date_edit.date().toString("yyyy-MM-dd")  # 如果使用 QDateEdit
            # 如果使用 QLineEdit，则是 remodel_date = self.remodel_date_edit.text().strip()
        else:
            remodel_date = ""
        manual_id = self.id_spin.value()
        ship_id = 0 if manual_id == 0 else manual_id

        # 从属性加成SpinBox收集值
        attr_kwargs = {}
        for key, spin in self.attr_spins.items():
            attr_kwargs[key] = spin.value()
        # 为满破阶段添加默认值0
        for base in [item[1] for item in self.tech_items]:
            attr_kwargs[f"tech_{base}_max"] = 0

        # 收集科技点总和
        tech_points_obtain = self.tech_points_obtain.value()
        tech_points_max = self.tech_points_max.value()
        tech_points_120 = self.tech_points_120.value()

        # 收集适用舰种
        tech_affects = [sc for sc, cb in self.affect_checkboxes.items() if cb.isChecked()]

        # 收集文本加成（如果保留文本输入框）
        bonus_obtain = []
        bonus_120 = []
        
        # 合并所有参数到字典
        ship_kwargs = {
            "id": ship_id,
            "name": self.name_edit.text(),
            "faction": self.faction_combo.currentText(),
            "ship_class": self.class_combo.currentText(),
            "rarity": self.rarity_combo.currentText(),
            "owned": False,
            "breakthrough": 0,
            "can_remodel": self.can_remodel_cb.isChecked(),
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
            "tech_affects": tech_affects,
            "tech_points_obtain": tech_points_obtain,
            "tech_points_max": tech_points_max,
            "tech_points_120": tech_points_120,
            "bonus_obtain": bonus_obtain,
            "bonus_120": bonus_120,
        }
        ship_kwargs.update(attr_kwargs)  # 将九属性字段合并进去

        ship = Ship(**ship_kwargs)
        print(f"新建舰船: id={ship.id}, name={ship.name}")
        print("新建船字典:", ship.to_dict())
        return ship