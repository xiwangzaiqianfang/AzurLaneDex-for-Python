from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QCheckBox, QSpinBox, QPushButton,
                               QGroupBox, QScrollArea, QGridLayout, QAbstractSpinBox, QFrame, QInputDialog, QLineEdit, QMessageBox, QDialog)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
import os
from gui.edit_ship_dialog import EditShipDialog

class DetailWidget(QWidget):
    data_changed = Signal(int, object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("编辑舰船")
        self.setObjectName("detailWidget")
        self.current_ship = None
        self.main_window = None
        self.manager = None
        self.setup_ui()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setSpacing(10)

        # ---- 立绘区域 ----
        pic_card = QFrame()
        pic_card.setObjectName("card")
        pic_layout = QVBoxLayout(pic_card)
        pic_layout.setContentsMargins(10, 10, 10, 10)
        #pic_card = QGroupBox("立绘")
        #pic_layout = QVBoxLayout(pic_group)
        pic_title = QLabel("立绘")
        pic_title.setObjectName("cardTitle")
        pic_layout.addWidget(pic_title)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(150)
        pic_layout.addWidget(self.image_label)
        #layout.addWidget(self.image_label)
        layout.addWidget(pic_card)

        # ---- 基本信息 ----
        basic_card = QFrame()
        basic_card.setObjectName("card") 
        card_layout = QVBoxLayout(basic_card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        #basic_group = QGroupBox("基本信息")
        title_label = QLabel("基本信息")
        title_label.setObjectName("cardTitle")
        title_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(title_label)
        form = QFormLayout()
        #form = QFormLayout(basic_group)
        form.setContentsMargins(0, 0, 0, 0)
        self.game_order_label = QLabel()
        self.id_label = QLabel()
        self.name_label = QLabel()
        self.faction_label = QLabel()
        self.class_label = QLabel()
        self.rarity_label = QLabel()
        form.addRow("图鉴顺序:", self.game_order_label)
        form.addRow("编号:", self.id_label)
        form.addRow("名称:", self.name_label)
        form.addRow("阵营:", self.faction_label)
        form.addRow("舰种:", self.class_label)
        form.addRow("稀有度:", self.rarity_label)
        card_layout.addLayout(form)
        #layout.addWidget(basic_group)
        layout.addWidget(basic_card)

        # ---- 状态操作 ----
        state_card = QFrame()
        state_card.setObjectName("card")
        state_layout = QVBoxLayout(state_card)
        state_layout.setContentsMargins(10, 10, 10, 10)

        state_title = QLabel("状态")
        state_title.setObjectName("cardTitle")
        state_layout.addWidget(state_title)

        # 水平布局放置复选框和突破控件
        hbox = QHBoxLayout()
        hbox.setSpacing(8)

        self.owned_cb = QCheckBox("已获得")
        self.owned_cb.clicked.connect(self.on_owned_clicked)
        hbox.addWidget(self.owned_cb)

        # 突破控件（水平布局）
        self.breakthrough_spin = QSpinBox()
        self.breakthrough_spin.setRange(0, 3)
        self.breakthrough_spin.setSuffix(" 破")
        self.breakthrough_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.breakthrough_spin.valueChanged.connect(self.on_breakthrough_changed)

        self.breakthrough_minus = QPushButton("-")
        self.breakthrough_plus = QPushButton("+")
        self.breakthrough_minus.clicked.connect(lambda: self.breakthrough_spin.setValue(self.breakthrough_spin.value() - 1))
        self.breakthrough_plus.clicked.connect(lambda: self.breakthrough_spin.setValue(self.breakthrough_spin.value() + 1))

        bt_layout = QHBoxLayout()
        bt_layout.setSpacing(2)
        bt_layout.addWidget(self.breakthrough_minus)
        bt_layout.addWidget(self.breakthrough_spin)
        bt_layout.addWidget(self.breakthrough_plus)
        hbox.addLayout(bt_layout)

        self.oath_cb = QCheckBox("已誓约")
        self.oath_cb.clicked.connect(self.on_oath_clicked)
        hbox.addWidget(self.oath_cb)

        self.level120_cb = QCheckBox("120级")
        self.level120_cb.clicked.connect(self.on_level120_clicked)
        hbox.addWidget(self.level120_cb)

        self.remodeled_cb = QCheckBox("已改造")
        self.remodeled_cb.clicked.connect(self.on_remodeled_clicked)
        hbox.addWidget(self.remodeled_cb)

        self.special_gear_obtained_cb = QCheckBox("已获得特殊兵装")
        self.special_gear_obtained_cb.clicked.connect(self.on_special_gear_obtained_clicked)
        hbox.addWidget(self.special_gear_obtained_cb)

        hbox.addStretch()
        state_layout.addLayout(hbox)
        layout.addWidget(state_card)

        # ---- 属性加成 (动态计算总和) ----
        #tech_group = QGroupBox("属性加成总和 (获得+满破+120级)")
        #tech_layout = QGridLayout(tech_group)

        #self.tech_labels = {}  # 存储每个科技项的QLabel

        #tech_list = [
        #    ("耐久", "tech_durability"),
        #    ("炮击", "tech_firepower"),
        #    ("雷击", "tech_torpedo"),
        #    ("防空", "tech_aa"),
        #    ("航空", "tech_aviation"),
        #    ("命中", "tech_accuracy"),
        #    ("装填", "tech_reload"),
        #    ("机动", "tech_mobility"),
        #    ("反潜", "tech_antisub")
        #]

        #for i, (display_name, base_name) in enumerate(tech_list):
        #    row = i // 3
        #    col = (i % 3) * 2
        #    label_name = QLabel(display_name + ":")
        #    label_value = QLabel("0")
        #    label_value.setAlignment(Qt.AlignRight)
        #    tech_layout.addWidget(label_name, row, col)
        #    tech_layout.addWidget(label_value, row, col+1)
        #    self.tech_labels[base_name] = label_value

        #layout.addWidget(tech_group)

        # ---- 科技点卡片 ----
        tech_card = QFrame()
        tech_card.setObjectName("card")
        tech_layout = QVBoxLayout(tech_card)
        tech_layout.setContentsMargins(10, 10, 10, 10)

        tech_title = QLabel("舰队科技")
        tech_title.setObjectName("cardTitle")
        tech_layout.addWidget(tech_title)
        #attr_group = QGroupBox("舰队科技")

        attr_form = QFormLayout()
        attr_form.setContentsMargins(0, 0, 0, 0)
        #attr_form = QFormLayout(attr_group)
        self.attr_bonus_label = QLabel()
        self.affects_label = QLabel()
        self.tech_points_total_label = QLabel()
        self.tech_obtain_label = QLabel()
        self.tech_120_label = QLabel()
        self.tech_max_label = QLabel()
        attr_form.addRow("科技点总和", self.tech_points_total_label)
        attr_form.addRow("获得科技点", self.tech_obtain_label)
        attr_form.addRow("满破科技点：", self.tech_max_label)
        attr_form.addRow("120级科技点：", self.tech_120_label)
        attr_form.addRow("属性加成：", self.attr_bonus_label)
        attr_form.addRow("适用舰种：", self.affects_label)
        tech_layout.addLayout(attr_form)
        #layout.addWidget(attr_group)
        layout.addWidget(tech_card)

        # ---- 获取方式 ----
        acquire_card = QFrame()
        acquire_card.setObjectName("card")
        acquire_layout = QVBoxLayout(acquire_card)
        acquire_layout.setContentsMargins(10, 10, 10, 10)

        #acquire_group = QGroupBox("获取方式")
        acquire_title = QLabel("获取方式")
        acquire_title.setObjectName("cardTitle")
        acquire_layout.addWidget(acquire_title)
        
        acquire_form = QFormLayout()
        acquire_form.setContentsMargins(0, 0, 0, 0)
        #acquire_form = QFormLayout(acquire_group)
        self.acquire_main_label = QLabel()
        self.acquire_detail_label = QLabel()
        self.build_time_label = QLabel()
        self.drop_locations_label = QLabel()
        self.drop_locations_label.setWordWrap(True)
        self.shop_exchange_label = QLabel()
        self.permanent_label = QLabel()
        acquire_form.addRow("主要获取:", self.acquire_main_label)
        acquire_form.addRow("详细信息:", self.acquire_detail_label)
        acquire_form.addRow("建造时间:", self.build_time_label)
        acquire_form.addRow("打捞地点:", self.drop_locations_label)
        acquire_form.addRow("商店兑换:", self.shop_exchange_label)
        acquire_form.addRow("是否常驻:", self.permanent_label)
        #layout.addWidget(acquire_group)
        acquire_layout.addLayout(acquire_form)

        layout.addWidget(acquire_card)

        # ---- 实装活动 ----
        event_card = QFrame()
        event_card.setObjectName("card")
        event_layout = QVBoxLayout(event_card)
        event_layout.setContentsMargins(10, 10, 10, 10)

        event_title = QLabel("实装活动")
        event_title.setObjectName("cardTitle")
        event_layout.addWidget(event_title)
        #event_group = QGroupBox("实装活动")
        #event_form = QFormLayout(event_group)
        event_form = QFormLayout()
        event_form.setContentsMargins(0, 0, 0, 0)
        self.debut_label = QLabel()
        self.release_date_label = QLabel()
        self.notes_label = QLabel()
        event_form.addRow("首次登场:", self.debut_label)
        event_form.addRow("实装时间:", self.release_date_label)
        self.remodel_date_label = QLabel()
        event_form.addRow("改造时间:", self.remodel_date_label)
        event_form.addRow("备注:", self.notes_label)
        #layout.addWidget(event_group)
        event_layout.addLayout(event_form)

        layout.addWidget(event_card)

        # ---- 特殊兵装卡片 ----
        self.gear_card = QFrame()
        self.gear_card.setObjectName("card")
        gear_layout = QVBoxLayout(self.gear_card)
        gear_layout.setContentsMargins(10, 10, 10, 10)

        gear_title = QLabel("特殊兵装")
        gear_title.setObjectName("cardTitle")
        gear_layout.addWidget(gear_title)

        gear_form = QFormLayout()
        self.gear_name_label = QLabel()
        self.gear_date_label = QLabel()
        self.gear_acquire_label = QLabel()
        gear_form.addRow("名称:", self.gear_name_label)
        gear_form.addRow("实装日期:", self.gear_date_label)
        gear_form.addRow("获取途径:", self.gear_acquire_label)
        gear_layout.addLayout(gear_form)

        layout.addWidget(self.gear_card)

        # 编辑按钮
        self.edit_btn = QPushButton("编辑详细信息")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        layout.addWidget(self.edit_btn)

        layout.addStretch()

    def set_ship(self, ship):
        #print(f"set_ship called with {ship}")
        self.current_ship = ship
        #print(f"current_ship {ship}")
        self.update_display()

    def clear(self):
        print("clear 被调用")
        self.current_ship = None
        self.game_order_label.clear()
        self.id_label.clear()
        self.name_label.clear()
        self.faction_label.clear()
        self.class_label.clear()
        self.rarity_label.clear()
        self.owned_cb.setChecked(False)
        self.remodeled_cb.setChecked(False)
        self.remodel_date_label.clear()
        self.oath_cb.setChecked(False)
        self.level120_cb.setChecked(False)
        self.breakthrough_spin.setValue(0)
        self.special_gear_obtained_cb.setChecked(False)
        #for label in self.tech_labels.values():
        #    label.setText("0")
        self.acquire_main_label.clear()
        self.acquire_detail_label.clear()
        self.build_time_label.clear()
        self.drop_locations_label.clear()
        self.shop_exchange_label.clear()
        self.permanent_label.clear()
        self.debut_label.clear()
        self.release_date_label.clear()
        self.notes_label.clear()
        if hasattr(self, 'gear_card'):
            self.gear_card.hide()
        self.image_label.clear()

    def update_display(self):
        #print(f"update_display: current_ship = {self.current_ship}")
        if not self.current_ship:
            return
        s = self.current_ship
        #print(f"update_display: ship {s.id}, owned={s.owned}, oath={s.oath}, level120={s.level_120}, bt={s.breakthrough}")

        # 设置值
        self.game_order_label.setText(str(s.game_order))
        self.id_label.setText(str(s.id))
        self.name_label.setText(s.name)
        self.faction_label.setText(s.faction)
        self.class_label.setText(s.ship_class)
        self.rarity_label.setText(s.rarity)

        # 状态
        self.owned_cb.setChecked(s.owned)
        self.remodeled_cb.setChecked(s.remodeled)
        self.oath_cb.setChecked(s.oath)
        self.level120_cb.setChecked(s.level_120)
        self.breakthrough_spin.setValue(s.breakthrough)
        self.special_gear_obtained_cb.setChecked(s.special_gear_obtained)

        # ---- 控件启用逻辑 ----
        owned = s.owned
        can_remodel = s.can_remodel
        can_special_gear = s.can_special_gear

        # 已改造：仅当已获得且可改造时启用
        self.remodeled_cb.setEnabled(owned and can_remodel)
        #self.special_gear_obtained_cb.setEnabled(owned and can_special_gear)
        self.special_gear_obtained_cb.setEnabled(s.can_special_gear)

        if s.remodel_date:
            self.remodel_date_label.setText(f"{s.remodel_date}")
        else:
            self.remodel_date_label.setText(" 无")

        # 其他状态控件：仅当已获得时启用
        self.oath_cb.setEnabled(owned)
        self.level120_cb.setEnabled(owned)
        self.breakthrough_spin.setEnabled(owned)
        self.breakthrough_minus.setEnabled(owned)
        self.breakthrough_plus.setEnabled(owned)

        # 显示属性加成
        attr_lines = []
        for base_display, base_key in [
            ("耐久", "durability"), ("炮击", "firepower"), ("雷击", "torpedo"),
            ("防空", "aa"), ("航空", "aviation"), ("命中", "accuracy"),
            ("装填", "reload"), ("机动", "mobility"), ("反潜", "antisub")
        ]:
            obtain = getattr(s, f"tech_{base_key}_obtain", 0)
            val_120 = getattr(s, f"tech_{base_key}_120", 0)
            if obtain != 0 or val_120 != 0:
                attr_lines.append(f"{base_display}: 获得{obtain}  120级{val_120}")
        if attr_lines:
            self.attr_bonus_label.setText("\n".join(attr_lines))
        else:
            self.attr_bonus_label.setText("无")

        # 显示适用舰种
        tech_affects = s.tech_affects
        if tech_affects is None or not isinstance(tech_affects, list):
            tech_affects = []
        affects = ", ".join(tech_affects) if tech_affects else "无限制"
        self.affects_label.setText(f"{affects}")

        # 显示科技点总和
        total_tech = s.tech_points_obtain + s.tech_points_max + s.tech_points_120
        self.tech_points_total_label.setText(f"{total_tech}")
        self.tech_obtain_label.setText(str(s.tech_points_obtain))
        self.tech_max_label.setText(str(s.tech_points_max))
        self.tech_120_label.setText(str(s.tech_points_120))

        # 获取方式
        self.acquire_main_label.setText(s.acquire_main)
        self.acquire_detail_label.setText(s.acquire_detail)
        self.build_time_label.setText(s.build_time)
        self.drop_locations_label.setText(", ".join(s.drop_locations))
        self.shop_exchange_label.setText(s.shop_exchange)
        self.permanent_label.setText("是" if s.is_permanent else "否")

        # 实装活动
        self.debut_label.setText(s.debut_event)
        self.release_date_label.setText(s.release_date)
        self.notes_label.setText(s.notes)

        s = self.current_ship
        has_gear = bool(s.special_gear_name or s.special_gear_date or s.special_gear_acquire)
        if has_gear:
            self.gear_name_label.setText(s.special_gear_name or "无")
            self.gear_date_label.setText(s.special_gear_date or "无")
            self.gear_acquire_label.setText(s.special_gear_acquire or "无")
            self.gear_card.show()
        else:
            self.gear_card.hide()

        # 立绘
        if s.image_path and os.path.exists(s.image_path):
            pixmap = QPixmap(s.image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(pixmap)
            else:
                self.image_label.setText("图片无法加载")
        else:
            self.image_label.setText("无立绘")

        #print(f"内容部件高度: {content.height()}, 滚动区域高度: {scroll.height()}")
        #if content.height() <= scroll.height():
        #    print("内容未超出滚动区域，无法滚动")

    def on_owned_clicked(self, checked):
        if not self.current_ship:
            return
        s = self.current_ship
        for attr in ['owned', 'oath', 'level_120', 'remodeled', 'can_remodel', 'can_special_gear', 'special_gear_obtained', 'is_permanent']:
            if hasattr(s, attr) and isinstance(getattr(s, attr), str):
                setattr(s, attr, getattr(s, attr).lower() == 'true')
        #print(f"on_owned_clicked: ship {self.current_ship.id}, checked={checked}")
        self.current_ship.owned = checked
        if not checked:  # 取消拥有时清零突破
            # 临时阻塞突破数信号，避免触发 on_breakthrough_changed
            self.breakthrough_spin.blockSignals(True)
            self.current_ship.breakthrough = 0
            self.breakthrough_spin.setValue(0)
            self.breakthrough_spin.blockSignals(False)
            self.current_ship.oath = False
            self.current_ship.level_120 = False
            self.current_ship.remodeled = False
            self.current_ship.special_gear_obtained = False
        self.data_changed.emit(self.current_ship.id, self.current_ship)
        self.update_display()

    def on_breakthrough_changed(self, value):
        if self.current_ship:
            self.current_ship.breakthrough = value
            #print(f"on_breakthrough_changed: ship {self.current_ship.id}, breakthrough={value}")
            self.data_changed.emit(self.current_ship.id, self.current_ship)

    def on_remodeled_clicked(self, checked):
        if self.current_ship:
            self.current_ship.remodeled = checked
            self.data_changed.emit(self.current_ship.id, self.current_ship)

    def on_oath_clicked(self, checked):
        if self.current_ship:
            self.current_ship.oath = checked
            self.data_changed.emit(self.current_ship.id,self.current_ship)

    def on_level120_clicked(self, checked):
        if self.current_ship:
            self.current_ship.level_120 = checked
            self.data_changed.emit(self.current_ship.id, self.current_ship)

    def on_special_gear_obtained_clicked(self, checked):
        if self.current_ship:
            self.current_ship.special_gear_obtained = checked
            self.data_changed.emit(self.current_ship.id, self.current_ship)

    def open_edit_dialog(self):
        # 尝试从主窗口获取当前选中的船
        #if self.parent() and hasattr(self.parent(), 'get_current_ship'):
        #    ship = self.parent().get_current_ship()
        #    if ship is None:
        #        print("无法获取当前选中的舰船")
        #        return
        #else:
            # 备用方案：使用当前保存的船
        #print("=== 进入 open_edit_dialog ===")
        #print(f"self.current_ship = {self.current_ship}")
        #print(f"self.main_window = {self.main_window}")
        ship = self.current_ship
        if ship is None and self.main_window:
            ship = self.main_window.get_current_ship()
        if ship is None:
            QMessageBox.warning(self, "错误", "无法获取当前选中的舰船。")
            return
        
        old_id = ship.id
        print("当前编辑的船 ID:", self.current_ship.id)

        # 密码验证等...
        if self.manager and self.manager.need_password_for_edit():
            pwd, ok = QInputDialog.getText(self, "验证", "请输入编辑密码:", QLineEdit.Password)
            if not ok or not self.manager.verify_edit_password(pwd):
                QMessageBox.warning(self, "错误", "密码错误，无法编辑。")
                return
            password_used = True
        else:
            password_used = False

        dlg = EditShipDialog(ship, parent=self)
        if dlg.exec() == QDialog.Accepted:
            changes = dlg.get_changes()
            if changes and self.manager:
                self.manager.log_edit(ship.id, changes, password_used)
            new_ship = dlg.get_ship()
            # 更新详情页的 current_ship
            self.current_ship = new_ship
            self.data_changed.emit(old_id, new_ship)
            QMessageBox.information(self, "成功", "舰船数据已更新。")