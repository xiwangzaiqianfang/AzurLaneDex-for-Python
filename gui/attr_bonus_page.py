from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
                               QGridLayout, QLabel, QFrame, QScrollArea, QPushButton,
                               QFileDialog, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class AttrBonusPage(QWidget):
    def __init__(self, manager, main_window):
        super().__init__()
        self.manager = manager
        self.main_window = main_window
        self.current_ship_class = "全舰种"  # 当前选择的舰种
        self.bonuses_cache = {}  # 缓存 {(舰种, 属性): 总值}
        self.setup_ui()
        self.load_data()
        # 监听数据变化，重新计算并刷新
        self.manager.data_changed.connect(self.on_data_changed)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 标题
        title = QLabel("属性加成")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)

        # 描述
        desc = QLabel("全舰队属性加成汇总（可按舰种筛选）")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 12px; color: #888; margin-bottom: 10px;")
        main_layout.addWidget(desc)

        # 舰种筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addStretch()
        filter_layout.addWidget(QLabel("筛选舰种:"))
        self.ship_class_combo = QComboBox()
        self.ship_class_combo.setMinimumWidth(200)
        # 获取所有舰种类别（从 manager 或预定义）
        self.ship_classes = ["全舰种", "驱逐", "轻巡", "重巡", "超巡", "战巡", "战列", "航战",
                             "航母", "轻航", "维修", "潜艇", "潜母", "运输", "风帆", "重炮", "其他"]
        self.ship_class_combo.addItems(self.ship_classes)
        self.ship_class_combo.currentTextChanged.connect(self.on_ship_class_changed)
        filter_layout.addWidget(self.ship_class_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        main_layout.addWidget(scroll)

        # 卡片容器
        self.card_container = QWidget()
        scroll.setWidget(self.card_container)

        # 网格布局
        self.grid_layout = QGridLayout(self.card_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # 属性列表（中文显示）
        self.attr_list = [
            "耐久", "炮击", "雷击", "防空", "航空",
            "命中", "装填", "机动", "反潜"
        ]

        # 存储卡片中的数值标签
        self.card_labels = {}

        # 导出按钮
        export_btn = QPushButton("导出为图片")
        export_btn.clicked.connect(self.export_as_image)
        main_layout.addWidget(export_btn, alignment=Qt.AlignCenter)

    def load_data(self):
        """计算并缓存 bonuses，然后刷新显示"""
        self.bonuses_cache = self.manager.calculate_global_bonuses()
        self.refresh_display()

    def refresh_display(self):
        """根据当前选择的舰种刷新卡片显示"""
        # 清空现有卡片
        self.clear_layout(self.grid_layout)

        # 获取当前选择的舰种
        selected = self.current_ship_class

        # 计算各属性的总和
        attr_totals = {attr: 0 for attr in self.attr_list}
        if selected == "全舰种":
            # 对所有舰种求和
            for (ship_class, attr), value in self.bonuses_cache.items():
                if attr in attr_totals:
                    attr_totals[attr] += value
        else:
            # 只取指定舰种
            for attr in self.attr_list:
                attr_totals[attr] = self.bonuses_cache.get((selected, attr), 0)

        # 创建卡片
        row, col = 0, 0
        max_cols = 3
        for attr, total in attr_totals.items():
            card = self.create_card(attr, total)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        self.grid_layout.setRowStretch(row + 1, 1)

    def create_card(self, attr, total):
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumWidth(150)
        card.setFixedHeight(100)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        attr_label = QLabel(attr)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        attr_label.setFont(font)
        layout.addWidget(attr_label)

        value_label = QLabel(str(total))
        value_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(value_label)
        return card

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def export_as_image(self):
        pixmap = self.grab()
        file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "attr_bonus.png", "PNG (*.png)")
        if file_path:
            if pixmap.save(file_path):
                QMessageBox.information(self, "成功", f"图片已保存至：{file_path}")
            else:
                QMessageBox.warning(self, "失败", "保存图片失败，请重试。")

    def on_ship_class_changed(self, text):
        self.current_ship_class = text
        self.refresh_display()

    def on_data_changed(self):
        """当管理器数据变化时（如用户修改拥有限制），重新计算并刷新"""
        self.load_data()