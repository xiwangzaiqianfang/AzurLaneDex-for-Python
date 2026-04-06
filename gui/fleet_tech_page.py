from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PySide6.QtCore import Qt

class FleetTechPage(QWidget):
    def __init__(self, manager, main_window):
        super().__init__()
        self.manager = manager
        self.main_window = main_window
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)

    def load_data(self):
        camp_tech = self.manager.calculate_camp_tech_points()
        global_bonuses = self.manager.calculate_global_bonuses()
        # 阵营科技点表格
        all_factions = ["白鹰", "皇家", "重樱", "铁血", "东煌", "撒丁帝国", "北方联合", "自由鸢尾", "维希教廷", "META", "其他"]
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["阵营", "获得科技点", "满破科技点", "120级科技点", "科技点总和"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setRowCount(len(all_factions))
        #camps = list(camp_tech.keys())
        total_sum = 0
        for row, camp in enumerate(all_factions):
            self.table.setItem(row, 0, QTableWidgetItem(camp))
            camp_tech = camp_tech.get(camp, {'obtain': 0, 'max': 0, 'level120': 0})
            obtain = camp_tech['obtain']
            max_bt = camp_tech['max']
            level120 = camp_tech['level120']
            camp_sum = obtain + max_bt + level120
            total_sum += camp_sum
            self.table.setItem(row, 1, QTableWidgetItem(str(obtain)))
            self.table.setItem(row, 2, QTableWidgetItem(str(max_bt)))
            self.table.setItem(row, 3, QTableWidgetItem(str(level120)))
            self.table.setItem(row, 4, QTableWidgetItem(str(camp_sum)))

        # 全舰队属性加成表格
        bonus_tab = QTableWidget()
        bonus_tab.setColumnCount(2)
        bonus_tab.setHorizontalHeaderLabels(["加成项", "总值"])
        bonus_tab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        items = [(f"{sc}-{attr}", value) for (sc, attr), value in global_bonuses.items()]
        bonus_tab.setRowCount(len(items))
        for row, (label, value) in enumerate(items):
            bonus_tab.setItem(row, 0, QTableWidgetItem(label))
            bonus_tab.setItem(row, 1, QTableWidgetItem(str(value)))

        total_label = QLabel(f"所有阵营科技点总和: {total_sum}")
        total_label.setStyleSheet("font-weight: bold;")