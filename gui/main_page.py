from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                               QDialog, QFileDialog, QMessageBox, QLabel,
                               QPushButton, QSizePolicy, QFrame)
from PySide6.QtCore import Qt
from gui.filter_bar import FilterBar
from gui.ship_list_widget import ShipListWidget
from gui.detail_widget import DetailWidget
from gui.add_ship_dialog import AddShipDialog

class MainPage(QWidget):
    def __init__(self, manager, main_window):
        super().__init__()
        self.manager = manager
        self.main_window = main_window
        self.current_sort_key = "id"
        self.current_sort_reverse = False
        self.setup_ui()
        self.setup_signals()
        self.apply_initial_data()

    def setup_ui(self):
        """构建主界面的所有控件和布局（原来 __init__ 中的内容）"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        # 顶部工具栏布局（包含筛选栏和主题切换按钮）
        self.filter_bar = FilterBar()
        #self.filter_bar.fleet_tech_clicked.connect(self.main_window.show_camp_tech)
        #self.filter_bar.attr_bonus_clicked.connect(self.main_window.show_attr_bonus)
        #self.filter_bar.theme_toggled.connect(self.main_window.toggle_theme)
        layout.addWidget(self.filter_bar)

        self.info_bar = QFrame()
        self.info_bar.setObjectName("infoBar")
        self.info_bar.setVisible(False)
        self.info_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_bar.setMinimumHeight(48)
        info_layout = QHBoxLayout(self.info_bar)
        info_layout.setContentsMargins(12, 8, 12, 8)
        info_layout.setSpacing(10)
        icon_label = QLabel("❗")
        icon_label.setStyleSheet("font-size: 18px;")
        info_layout.addWidget(icon_label)
        self.info_bar_msg = QLabel("您正在使用测试版本，部分功能可能不稳定，请谨慎使用。")
        info_layout.addWidget(self.info_bar_msg)
        info_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(lambda: self.info_bar.hide())
        info_layout.addWidget(close_btn)
        layout.addWidget(self.info_bar)

        # 分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(0)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter, 1)  # 拉伸因子1

        self.ship_list = ShipListWidget()
        self.splitter.addWidget(self.ship_list)

        # 右侧详情
        self.detail_widget = DetailWidget()
        self.detail_widget.main_window = self.main_window
        self.splitter.addWidget(self.detail_widget)

        self.splitter.setSizes([450, 850])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        
        self.ship_list.setMinimumWidth(0)
        self.check_and_show_test_version_info()

    def setup_signals(self):
        self.filter_bar.filter_changed.connect(self.apply_filter)
        self.filter_bar.reset_clicked.connect(self.reset_filter)
        #self.filter_bar.stat_clicked.connect(self.show_stat_dialog)
        self.filter_bar.add_ship_clicked.connect(self.show_add_ship_dialog)
        self.filter_bar.switch_file_clicked.connect(self.switch_file)
        self.filter_bar.export_clicked.connect(self.export_data)
        self.filter_bar.import_clicked.connect(self.import_data)
        #self.filter_bar.update_online_clicked.connect(self.update_online)
        self.filter_bar.sort_order_changed.connect(self.on_sort_order_changed)
        self.filter_bar.batch_operation_signal.connect(self.batch_operation)

        self.filter_bar.main_window = self.main_window
        self.filter_bar.manager = self.manager

        self.ship_list.current_ship_changed.connect(self.on_ship_selected)
        self.ship_list.sort_requested.connect(self.on_sort_requested)
        self.detail_widget.data_changed.connect(self.on_ship_updated)

    def apply_initial_data(self):
        ship_names = [ship.name for ship in self.manager.ships]
        gear_names = [ship.special_gear_name for ship in self.manager.ships if ship.special_gear_name]
        self.filter_bar.set_completer_items(ship_names, gear_names)
        self.apply_filter({})

    def apply_filter(self, criteria):
        print(f"筛选条件: {criteria}")
        current_ship_id = None
        if hasattr(self, 'ship_list') and hasattr(self.ship_list, 'get_current_ship'):
            current_ship = self.ship_list.get_current_ship()
            if current_ship:
                current_ship_id = current_ship.id
        
        filtered = self.manager.filter(criteria)
        # 排序（默认按编号）
        #print(f"筛选后舰船数: {len(filtered)}")
        filtered = self.manager.sort(filtered, key=self.current_sort_key, reverse=self.current_sort_reverse)
        self.ship_list.set_ships(filtered)

        if filtered:
            if current_ship_id is not None:
                for i, ship in enumerate(filtered):
                    if ship.id == current_ship_id:
                        self.ship_list.selectRow(i)
                        break
                else:
                    self.ship_list.selectRow(0)   # 默认选中第一项
            else:
                self.ship_list.selectRow(0)
        else:
            self.detail_widget.clear()

    def reset_filter(self):
        self.filter_bar.reset()
        self.apply_filter({})

    def on_ship_updated(self, old_id, new_ship):
        print("接收到更新信号，旧 ID:", old_id, "新船:", new_ship)
        if new_ship is None:
            return
        # 更新数据管理器中的对应船
        old_ship = self.detail_widget.current_ship
        if old_ship is None:
            print("无法获取当前选中的舰船")
            return
        success = self.manager.update_ship(old_id, new_ship)
        if not success:
            print("更新失败，可能用户取消了冲突处理")
            return
        # 更新补全列表（如果名字或特殊兵装有变动）
        ship_names = [ship.name for ship in self.manager.ships]
        gear_names = [ship.special_gear_name for ship in self.manager.ships if ship.special_gear_name]
        self.filter_bar.set_completer_items(ship_names, gear_names)
        # 更新左侧列表显示
        self.apply_filter(self.filter_bar.get_current_criteria())
        # 如果当前详情页显示的正是这艘船，刷新详情页
        if self.detail_widget.current_ship and self.detail_widget.current_ship.id == new_ship.id:
            self.detail_widget.set_ship(new_ship)
        #for i, s in enumerate(self.manager.ships):
        #    if s.id == new_ship.id:
        #        self.manager.ships[i] = new_ship
        #        break
        #self.manager.save()

    def on_sort_order_changed(self, key, reverse):
        """用户改变排序方式时，重新排序当前列表"""
        # 获取当前显示的舰船列表（即已经过筛选的列表）
        self.current_sort_key = key
        self.current_sort_reverse = reverse
        current_ships = self.ship_list.current_ships
        sorted_ships = self.manager.sort(current_ships, key, reverse)
        self.ship_list.set_ships(sorted_ships)
        # 注意：由于排序改变了列表顺序，但筛选条件未变，我们不需要重新应用筛选。
        # 同时，当前选中的船可能改变，但 set_ships 会自动选中第一行。

    def on_sort_requested(self, key, reverse):
        filtered = self.ship_list.current_ships  # 当前显示的列表
        sorted_ships = self.manager.sort(filtered, key, reverse)
        self.ship_list.set_ships(sorted_ships)

    def show_add_ship_dialog(self):
        if getattr(self, '_adding_ship', False):
            return
        self._adding_ship = True
        try:
            print("打开新增舰船对话框")
            dlg = AddShipDialog(self)
            if dlg.exec() == QDialog.Accepted:
                print("用户点击确定")
                new_ship = dlg.get_ship()
                if new_ship is None:
                    return
                print(f"获取到新船: {new_ship.name}")
                self.manager.add_ship(new_ship)
                ship_names = [ship.name for ship in self.manager.ships]
                gear_names = [ship.special_gear_name for ship in self.manager.ships if ship.special_gear_name]
                self.filter_bar.set_completer_items(ship_names, gear_names)
                print("已调用 manager.add_ship")
                # 刷新列表（可能需要重新应用当前筛选）
                self.apply_filter(self.filter_bar.get_current_criteria())
            else:
                print("用户取消")
        finally:
                self._adding_ship = False

    def switch_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 JSON 数据文件", "", "JSON (*.json)")
        if path:
            try:
                self.manager.switch_file(path)
                ship_names = [ship.name for ship in self.manager.ships]
                self.filter_bar.set_ship_names(ship_names)
                self.apply_filter({})
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载文件失败: {e}")

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出数据", "", "CSV (*.csv);;Excel (*.xlsx)")
        if path:
            if path.endswith('.csv'):
                self.manager.export_csv(path)
                ship_names = [ship.name for ship in self.manager.ships]
                self.filter_bar.set_ship_names(ship_names)
            elif path.endswith('.xlsx'):
                self.manager.export_excel(path)
                ship_names = [ship.name for ship in self.manager.ships]
                self.filter_bar.set_ship_names(ship_names)
            QMessageBox.information(self, "完成", "导出成功！")

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入数据", "", "CSV (*.csv);;Excel (*.xlsx)")
        if path:
            try:
                self.manager.import_csv(path)  # 仅支持 CSV，Excel 也可用 pandas 读取
                ship_names = [ship.name for ship in self.manager.ships]
                self.filter_bar.set_ship_names(ship_names)
                self.apply_filter({})
                QMessageBox.information(self, "完成", "导入成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")

    
    def batch_operation(self, op, criteria):
        # 优先获取勾选的舰船ID
        checked_ids = self.ship_list.get_checked_ship_ids()
        if checked_ids:
            # 根据ID获取对应的Ship对象
            ships_to_modify = [ship for ship in self.manager.ships if ship.id in checked_ids]
            source_desc = f"勾选的 {len(ships_to_modify)} 艘舰船"
        else:
            # 根据筛选条件获取需要修改的舰船列表
            ships_to_modify = self.manager.filter(criteria)   # 注意：filter 返回的是符合条件的船列表
            source_desc = f"筛选条件下的 {len(ships_to_modify)} 艘舰船"
        if not ships_to_modify:
            QMessageBox.information(self, "提示", "当前筛选条件下没有舰船。")
            self.apply_filter(self.filter_bar.get_current_criteria())
            return
        
        op_desc = {
            "owned_true": "设为已获得",
            "owned_false": "设为未获得",
            "oath_true": "设为誓约",
            "oath_false": "取消誓约",
            "max_true": "设为满破",
            "max_false": "取消满破",
            "120_true": "设为120级",
            "120_false": "取消120级",
            "remodeled_true": "设为已改造",
            "remodeled_false": "取消改造",
            "special_gear_obtained_true": "设为拥有特殊兵装",
            "special_gear_obtained_false": "设为未拥有特殊兵装",
        }.get(op, op)

        # 确认对话框
        reply = QMessageBox.question(self, "批量操作确认",
                                     f"将对 {len(ships_to_modify)} 艘舰船执行操作：{op}。是否继续？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        # 执行修改
        modified_count = 0
        for ship in ships_to_modify:
            if op == "owned_true":
                ship.owned = True
                modified_count += 1
            elif op == "owned_false":
                ship.owned = False
                # 如果取消拥有，同时清空其他状态（可选）
                ship.breakthrough = 0
                ship.oath = False
                ship.level_120 = False
                ship.remodeled = False
                modified_count += 1
            elif op == "oath_true":
                ship.oath = True
                modified_count += 1
            elif op == "oath_false":
                ship.oath = False
                modified_count += 1
            elif op == "max_true":
                ship.breakthrough = 3
                modified_count += 1
            elif op == "max_false":
                ship.breakthrough = 0
                modified_count += 1
            elif op == "120_true":
                ship.level_120 = True
                modified_count += 1
            elif op == "120_false":
                ship.level_120 = False
                modified_count += 1
            elif op == "remodeled_true":
                if ship.can_remodel:
                    ship.remodeled = True
                    modified_count += 1
                else:
                    pass
            elif op == "remodeled_false":
                ship.remodeled = False
                modified_count += 1
            elif op == "special_gear_obtained_true":
                ship.special_gear_obtained = True
                modified_count += 1
            elif op == "special_gear_obtained_false":
                ship.special_gear_obtained = False
                modified_count += 1

        self.manager.save()
        if checked_ids:
            self.ship_list.clear_checks()
        # 刷新界面：重新应用筛选（列表更新）并刷新详情页
        self.apply_filter(self.filter_bar.get_current_criteria())
        QMessageBox.information(self, "完成", f"已批量修改 {len(ships_to_modify)} 艘舰船。")

    def on_ship_selected(self, ship):
        #print(f"on_ship_selected: ship = {ship}")
        if ship:
            self.detail_widget.set_ship(ship)
        else:
            self.detail_widget.clear()

    def check_and_show_test_version_info(self):
        version = self.manager.get_program_version()
        # 判断是否为测试版本（版本号包含 beta、test、dev、alpha 等）
        test_keywords = ['beta', 'test', 'dev', 'alpha']
        is_test = any(keyword in version.lower() for keyword in test_keywords)
        if is_test:
            self.info_bar.setVisible(True)
        else:
            self.info_bar.setVisible(False)