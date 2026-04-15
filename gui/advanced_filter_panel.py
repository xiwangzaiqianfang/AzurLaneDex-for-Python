# gui/advanced_filter_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QCheckBox,
                               QScrollArea, QFrame, QHBoxLayout, QLabel,
                               QGridLayout)
from PySide6.QtCore import Signal, Qt

class AdvancedFilterPanel(QWidget):
    filter_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool)
        self.setWindowTitle("高级筛选")
        self.resize(400, 500)
        self.setObjectName("advancedFilterPanel")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        main_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        # 1. 舰种卡片
        self.ship_class_card = self._create_card("舰种")
        self.ship_class_checkboxes = {}
        class_options = ["前排先锋", "后排主力", "驱逐", "轻巡", "重巡", "战列", "航母", "维修", "潜艇", "其他"]
        self._add_checkboxes_to_grid(self.ship_class_card, class_options, self.ship_class_checkboxes, columns=3)
        layout.addWidget(self.ship_class_card)

        # 2. 阵营卡片
        self.faction_card = self._create_card("阵营")
        self.faction_checkboxes = {}
        faction_options = ["全阵营", "白鹰", "皇家", "重樱", "铁血", "东煌", "撒丁帝国",
                           "北方联合", "自由鸢尾", "维希教廷", "郁金王国", "META", "飓风", "其他"]
        self._add_checkboxes_to_grid(self.faction_card, faction_options, self.faction_checkboxes, columns=3)
        # 全阵营互斥
        self.faction_checkboxes["全阵营"].toggled.connect(self._on_all_faction_toggled)
        layout.addWidget(self.faction_card)

        # 3. 稀有度卡片
        self.rarity_card = self._create_card("稀有度")
        self.rarity_checkboxes = {}
        rarity_options = ["全部", "普通", "稀有", "精锐", "超稀有", "海上传奇"]
        self._add_checkboxes_to_grid(self.rarity_card, rarity_options, self.rarity_checkboxes, columns=3)
        self.rarity_checkboxes["全部"].toggled.connect(self._on_all_rarity_toggled)
        layout.addWidget(self.rarity_card)

        # 4. 附加状态卡片
        self.extra_card = self._create_card("附加状态")
        self.extra_checkboxes = {}
        extra_options = [
            "可改造", "未改造", "已改造",
            "已满破", "未满破",
            "已120级", "未120级",
            "特殊(μ兵装/小船)",
            "可拥有特殊兵装", "未拥有特殊兵装", "已拥有特殊兵装",
            "未誓约", "已誓约",
            "已常驻", "未常驻"
        ]
        self._add_checkboxes_to_grid(self.extra_card, extra_options, self.extra_checkboxes, columns=3)
        layout.addWidget(self.extra_card)

        # 5. 属性加成卡片
        self.attr_card = self._create_card("属性加成")
        self.attr_checkboxes = {}
        attr_options = ["炮击", "航空", "机动", "防空", "雷击", "装填", "耐久", "反潜"]
        self._add_checkboxes_to_grid(self.attr_card, attr_options, self.attr_checkboxes, columns=3)
        layout.addWidget(self.attr_card)

        layout.addStretch()

    def _create_card(self, title):
        """创建卡片样式容器"""
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        card_layout.addWidget(title_label)
        return card
    
    def _add_checkboxes_to_grid(self, card, options, checkboxes_dict, columns=3):
        """在卡片的布局中添加网格布局，放置复选框"""
        # 获取卡片的已有布局（垂直布局）
        card_layout = card.layout()
        grid = QGridLayout()
        grid.setSpacing(5)
        for i, opt in enumerate(options):
            cb = QCheckBox(opt)
            cb.stateChanged.connect(self._on_filter_changed)
            row = i // columns
            col = i % columns
            grid.addWidget(cb, row, col)
            checkboxes_dict[opt] = cb
        card_layout.addLayout(grid)

    def _on_filter_changed(self):
        criteria = self.get_criteria()
        self.filter_changed.emit(criteria)

    def _on_all_faction_toggled(self, checked):
        if checked:
            for opt, cb in self.faction_checkboxes.items():
                if opt != "全阵营":
                    cb.setChecked(False)
        # 如果取消全阵营，不做自动处理

    def _on_all_rarity_toggled(self, checked):
        if checked:
            for opt, cb in self.rarity_checkboxes.items():
                if opt != "全部":
                    cb.setChecked(False)
        else:
            # 如果取消全部，保留其他选项
            pass

    def get_criteria(self):
        criteria = {}

        # 舰种
        selected_classes = [opt for opt, cb in self.ship_class_checkboxes.items() if cb.isChecked()]
        if selected_classes:
            criteria['ship_class'] = selected_classes

        # 阵营
        selected_factions = [opt for opt, cb in self.faction_checkboxes.items() if cb.isChecked()]
        if selected_factions and "全阵营" not in selected_factions:
            criteria['faction'] = selected_factions

        # 稀有度
        selected_rarities = [opt for opt, cb in self.rarity_checkboxes.items() if cb.isChecked()]
        if selected_rarities and "全部" not in selected_rarities:
            criteria['rarity'] = selected_rarities

        # 附加索引
        extra_map = {
            "可改造": "can_remodel",
            "未改造": "can_remodel_not",
            "已改造": "remodeled",
            "已满破": "max_breakthrough",
            "未满破": "not_max",
            "已120级": "level_120",
            "未120级": "not_level120",
            "特殊(μ兵装/小船)": "is_special",
            "可拥有特殊兵装": "can_special_gear",
            "未拥有特殊兵装": "can_special_gear_not_obtained",
            "已拥有特殊兵装": "special_gear_obtained",
            "未誓约": "not_oath",
            "已誓约": "oath",
            "已常驻": "is_permanent",
            "未常驻": "not_permanent"
        }
        for opt, cb in self.extra_checkboxes.items():
            if cb.isChecked():
                key = extra_map.get(opt)
                if key:
                    criteria[key] = True

        # 属性加成（只要舰船有任意一项属性加成大于0？用户可能希望筛选出拥有特定属性加成的船，但属性加成是数值，需要更复杂的判断。这里简化：筛选出拥有该属性加成的船（即 tech_xxx_obtain + tech_xxx_120 > 0））
        selected_attrs = [opt for opt, cb in self.attr_checkboxes.items() if cb.isChecked()]
        if selected_attrs:
            criteria['attributes'] = selected_attrs

        return criteria

    def reset(self):
        for group in [self.ship_class_checkboxes, self.faction_checkboxes,
                      self.rarity_checkboxes, self.extra_checkboxes, self.attr_checkboxes]:
            for cb in group.values():
                cb.setChecked(False)
        # 特殊处理全阵营和全部稀有度不会被自动勾选，所以不需要额外操作
        self._on_filter_changed()