from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGridLayout, QLabel
from PySide6.QtCore import Signal, Qt

class AdvancedFilterPanel(QWidget):
    filter_changed = Signal(dict)  # 复选框变化时发射

    def __init__(self, current_criteria=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool)
        self.setWindowTitle("高级筛选")
        self.setObjectName("advancedFilterPanel")
        self.resize(260, 200)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        title_label = QLabel("高级筛选")
        title_label.setObjectName("panelTitle")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(8)

        checkboxes = [
            (0, 0, "已获得", "owned"),
            (0, 1, "未获得", "not_owned"),
            (1, 0, "可改造", "can_remodel"),
            (1, 1, "已改造", "remodeled"),
            (2, 0, "未改造", "can_remodel_not"),
            (2, 1, "已誓约", "oath"),
            (3, 0, "已满破", "max_breakthrough"),
            (3, 1, "未满破", "not_max"),
            (4, 0, "120级", "level_120"),
            (4, 1, "未120级", "not_level120")
        ]

        
        # 创建复选框
        #self.owned_cb = QCheckBox("已获得")
        #self.not_owned_cb = QCheckBox("未获得")
        #self.remodel_cb = QCheckBox("可改造")
        #self.remodeled_cb = QCheckBox("已改造")
        #self.can_remodel_not_cb = QCheckBox("未改造")
        #self.oath_cb = QCheckBox("已誓约")
        #self.max_cb = QCheckBox("已满破")
        #self.not_max_cb = QCheckBox("未满破")
        #self.level120_cb = QCheckBox("120级")
        #self.not_level120_cb = QCheckBox("未120级")

        # 将所有复选框添加到布局
        self.checkboxes = {}
        for row, col, text, key in checkboxes:
            cb = QCheckBox(text)
            cb.stateChanged.connect(self._on_checkbox_changed)
            grid.addWidget(cb, row, col)
            self.checkboxes[key] = cb
        #for cb in [self.owned_cb, self.not_owned_cb, self.remodel_cb, self.remodeled_cb,
        #           self.can_remodel_not_cb, self.oath_cb, self.max_cb, self.not_max_cb,
        #           self.level120_cb, self.not_level120_cb]:
        #    cb.stateChanged.connect(self._on_checkbox_changed)  # 关键：连接信号
        #    layout.addWidget(cb)
        main_layout.addLayout(grid)
        main_layout.addStretch()

        #layout.addStretch()

        # 如果传入初始筛选条件，设置复选框状态
        if current_criteria is not None and isinstance(current_criteria, dict):
            self.set_criteria(current_criteria)

    def _on_checkbox_changed(self):
        """任意复选框变化时，收集状态并发射信号"""
        criteria = {}
        for key, cb in self.checkboxes.items():
            if cb.isChecked():
                # 将键名转换为与 manager.py 一致的名称（注意映射）
                if key == "owned":
                    criteria['owned'] = True
                elif key == "not_owned":
                    criteria['not_owned'] = True
                elif key == "can_remodel":
                    criteria['can_remodel'] = True
                elif key == "remodeled":
                    criteria['remodeled'] = True
                elif key == "can_remodel_not":
                    criteria['can_remodel_not'] = True
                elif key == "oath":
                    criteria['oath'] = True
                elif key == "max_breakthrough":
                    criteria['max_breakthrough'] = True
                elif key == "not_max":
                    criteria['not_max'] = True
                elif key == "level_120":
                    criteria['level_120'] = True
                elif key == "not_level120":
                    criteria['not_level120'] = True
        #if self.owned_cb.isChecked():
        #    criteria['owned'] = True
        #if self.not_owned_cb.isChecked():
        #    criteria['not_owned'] = True
        #if self.remodel_cb.isChecked():
        #    criteria['can_remodel'] = True
        #if self.remodeled_cb.isChecked():
        #    criteria['remodeled'] = True
        #if self.can_remodel_not_cb.isChecked():
        #    criteria['can_remodel_not'] = True
        #if self.oath_cb.isChecked():
        #    criteria['oath'] = True
        #if self.max_cb.isChecked():
        #    criteria['max_breakthrough'] = True
        #if self.not_max_cb.isChecked():
        #    criteria['not_max'] = True
        #if self.level120_cb.isChecked():
        #    criteria['level_120'] = True
        #if self.not_level120_cb.isChecked():
        #    criteria['not_level120'] = True
        self.filter_changed.emit(criteria)
        #print("高级面板发射条件:", criteria)  # 调试输出

    def set_criteria(self, criteria):
        """根据字典设置复选框状态（用于初始化或重置）"""
        for key, cb in self.checkboxes.items():
            cb.setChecked(criteria.get(key, False))
        #self.owned_cb.setChecked(criteria.get('owned', False))
        #self.not_owned_cb.setChecked(criteria.get('not_owned', False))
        #self.remodel_cb.setChecked(criteria.get('can_remodel', False))
        #self.remodeled_cb.setChecked(criteria.get('remodeled', False))
        #self.can_remodel_not_cb.setChecked(criteria.get('can_remodel_not', False))
        #self.oath_cb.setChecked(criteria.get('oath', False))
        #self.max_cb.setChecked(criteria.get('max_breakthrough', False))
        #self.not_max_cb.setChecked(criteria.get('not_max', False))
        #self.level120_cb.setChecked(criteria.get('level_120', False))
        #self.not_level120_cb.setChecked(criteria.get('not_level120', False))

    def closeEvent(self, event):
        """关闭时隐藏（不销毁），下次点击按钮可直接显示"""
        self.hide()
        event.ignore()