from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class StatPage(QWidget):
    def __init__(self, manager, main_window):
        super().__init__()
        self.manager = manager
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        self.load_stats()

    def load_stats(self):
        stats_dict = self.manager.stats()
        text = (
            f"总计舰船数: {stats_dict['total']}\n"
            f"已获得: {stats_dict['owned']}\n"
            f"未获得: {stats_dict['not_owned']}\n"
            f"已满破: {stats_dict['max_break']}\n"
            f"未满破: {stats_dict['not_max']}\n"
            f"已誓约: {stats_dict['oath']}\n"
            f"已改造: {stats_dict['remodeled']}\n"
            f"可改造未改造: {stats_dict['can_remodel_not']}\n"
            f"120级: {stats_dict['level120']}\n"
        )
        self.stats_label.setText(text)