from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QComboBox, QCheckBox, QDialogButtonBox, QTextEdit, QGroupBox, QGridLayout, QSpinBox, QScrollArea,
                               QLabel, QWidget, QHBoxLayout, QPushButton, QAbstractSpinBox, QDateEdit, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QDate
from gui.add_ship_dialog import AddShipDialog
from models import Ship

class EditShipDialog(AddShipDialog):
    def __init__(self, ship: Ship, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"编辑舰船 - {ship.name}")
        self.ship = ship
        self.load_ship_data()

    def load_ship_data(self):
        """将现有船的数据填入各个控件"""
        self.game_order_spin.setValue(self.ship.game_order)
        self.id_spin.setValue(self.ship.id)
        self.name_edit.setText(self.ship.name)
        self.alt_name_edit.setText(self.ship.alt_name)
        self.faction_combo.setCurrentText(self.ship.faction)
        self.class_combo.setCurrentText(self.ship.ship_class)
        self.rarity_combo.setCurrentText(self.ship.rarity)
        self.can_remodel_cb.setChecked(self.ship.can_remodel)
        if self.ship.remodel_date:
            self.remodel_date_edit.setDate(QDate.fromString(self.ship.remodel_date, "yyyy-MM-dd"))
        self.acquire_main_edit.setText(self.ship.acquire_main)
        self.acquire_detail_edit.setText(self.ship.acquire_detail)
        self.build_time_edit.setText(self.ship.build_time)
        self.drop_locations_edit.setText(";".join(self.ship.drop_locations))
        self.shop_exchange_edit.setText(self.ship.shop_exchange)
        self.is_permanent_cb.setChecked(self.ship.is_permanent)
        self.debut_event_edit.setText(self.ship.debut_event)
        self.release_date_edit.setDate(QDate.fromString(self.ship.release_date, "yyyy-MM-dd"))
        self.notes_edit.setText(self.ship.notes)
        self.can_special_gear_cb.setChecked(self.ship.can_special_gear)
        self.special_gear = bool(self.ship.special_gear_name or self.ship.special_gear_date or self.ship.special_gear_acquire)
        self.toggle_special_gear()
        self.special_gear_name_edit.setText(self.ship.special_gear_name)
        if self.ship.special_gear_date:
            self.special_gear_date_edit.setDate(QDate.fromString(self.ship.special_gear_date, "yyyy-MM-dd"))
        self.special_gear_acquire_edit.setText(self.ship.special_gear_acquire)
        self.image_path_edit.setText(self.ship.image_path)

        # 属性加成
        # 获得时加成
        if self.ship.obtain_bonus_attr:
            rb = self.obtain_attr_radios.get(self.ship.obtain_bonus_attr)
            if rb:
                rb.setChecked(True)
        self.obtain_value_spin.setValue(self.ship.obtain_bonus_value)
        for sc in self.ship.obtain_affects:
            cb = self.obtain_affect_checkboxes.get(sc)
            if cb:
                cb.setChecked(True)

        # 120级时加成
        if self.ship.level120_bonus_attr:
            rb = self.level120_attr_radios.get(self.ship.level120_bonus_attr)
            if rb:
                rb.setChecked(True)
        self.level120_value_spin.setValue(self.ship.level120_bonus_value)
        for sc in self.ship.level120_affects:
            cb = self.level120_affect_checkboxes.get(sc)
            if cb:
                cb.setChecked(True)

        # 科技点总和
        self.tech_points_obtain.setValue(self.ship.tech_points_obtain)
        self.tech_points_max.setValue(self.ship.tech_points_max)
        self.tech_points_120.setValue(self.ship.tech_points_120)

        # 适用舰种
        for sc in self.ship.obtain_affects:
            if sc in self.obtain_affect_checkboxes:
                self.obtain_affect_checkboxes[sc].setChecked(True)
        for sc in self.ship.level120_affects:
            if sc in self.level120_affect_checkboxes:
                self.level120_affect_checkboxes[sc].setChecked(True)

        # 其他状态（如 owned 等）在编辑时通常不修改，保持原样
        # 但也可以开放，根据需要决定

    def get_changes(self):
        """返回修改的字段字典，用于日志"""
        new_ship = self.get_ship()
        changes = {}
        for field in Ship.__dataclass_fields__.keys():
            old_val = getattr(self.ship, field)
            new_val = getattr(new_ship, field)
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
        return changes

    def get_ship(self):
        """复用父类的 get_ship，但返回新的 Ship 对象，不自动分配 ID"""
        # 调用父类方法，但跳过 ID 自动分配部分
        # 可以直接复用，只需确保 id 从原船保留
        if self.faction_combo.currentText() == "请选择" or \
            self.class_combo.currentText() == "请选择" or \
            self.rarity_combo.currentText() == "请选择":
                return None
        manual_id = self.id_spin.value()
        ship_id = 0 if manual_id == 0 else manual_id
        game_order = self.game_order_spin.value()
        can_remodel = self.can_remodel_cb.isChecked()
        can_remodel = self.can_remodel_cb.isChecked()
        remodel_date = self.remodel_date_edit.date().toString("yyyy-MM-dd") if can_remodel else ""
        # 获得时加成的属性与数值
        obtain_bonus_attr = ""
        for attr, rb in self.obtain_attr_radios.items():
            if rb.isChecked():
                obtain_bonus_attr = attr
                break
        obtain_bonus_value = self.obtain_value_spin.value()
        obtain_affects = [sc for sc, cb in self.obtain_affect_checkboxes.items() if cb.isChecked()]

        # 120级时加成的属性与数值
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

        # 特殊兵装
        if self.can_special_gear_cb.isChecked():
            special_gear_name = self.special_gear_name_edit.text()
            special_gear_date = self.special_gear_date_edit.date().toString("yyyy-MM-dd")
            special_gear_acquire = self.special_gear_acquire_edit.text()
        else:
            special_gear_name = special_gear_date = special_gear_acquire = ""
        
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
            "tech_affects": [],                     # 已废弃，留空
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
        return ship