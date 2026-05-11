from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QColor, QBrush

class ShipListWidget(QTableWidget):
    current_ship_changed = Signal(object)   # 发出 Ship 对象
    sort_requested = Signal(str, bool)      # (key, reverse)
    mark_owned_requested = Signal(int, bool)          # (ship_id, owned)
    mark_max_breakthrough_requested = Signal(int, bool)  # (ship_id, max)
    mark_level120_requested = Signal(int, bool)        # (ship_id, level120)
    mark_oath_requested = Signal(int, bool)            # (ship_id, oath)
    delete_ship_requested = Signal(int)                # (ship_id) 仅开发模式

    def __init__(self, dev_mode=False, account_manager=None):
        super().__init__()
        self.dev_mode = dev_mode
        self.account_manager = account_manager
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(["","编号", "名称", "拥有", "突破", "誓约", "120级"])
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionsClickable(False)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(1, 50)
        #self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 50)
        self.setColumnWidth(4, 50)
        self.setColumnWidth(5, 50)
        self.setColumnWidth(6, 50)
        self.setWordWrap(False)
        self.horizontalHeader().setSortIndicatorShown(True)
        self.horizontalHeader().sortIndicatorChanged.connect(self.on_sort_indicator_changed)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        #self.itemSelectionChanged.connect(self.on_selection_changed)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        #self.setDragEnabled(False)          # 允许拖动选择（不影响触摸滚动）
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)  # 平滑滚动
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.current_item_timer = QTimer()
        self.current_item_timer.setSingleShot(True)
        self.current_item_timer.timeout.connect(self._delayed_current_item_changed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # 连接 currentItemChanged 而不是 itemSelectionChanged 消除延迟
        self.currentItemChanged.connect(self.on_current_item_changed)

        self.current_ships = []  # 当前显示的 Ship 对象列表，与行对应

    def set_ships(self, ships):
        #self.itemSelectionChanged.disconnect(self.on_selection_changed)
        
        self.current_ships = ships
        self.setRowCount(len(ships))
        for row, ship in enumerate(ships):
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setData(Qt.UserRole, "checkbox")
            check_item.setCheckState(Qt.Unchecked)
            self.setItem(row, 0, check_item)
            self.setItem(row, 1, QTableWidgetItem(str(ship.id)))
            #self.setItem(row, 2, QTableWidgetItem(ship.name))
            display_name = ship.name
            if ship.alt_name:
                display_name = f"{ship.name}（{ship.alt_name}）"
            name_item = QTableWidgetItem(display_name)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_item.setToolTip(ship.name)
            self.setItem(row, 2, name_item)
            owned_item = QTableWidgetItem("✓" if ship.owned else "✗")
            owned_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 3, owned_item)

            bt_text = str(ship.breakthrough)
            if ship.is_max_breakthrough():
                bt_text = "满破"
            elif ship.breakthrough == 0:
                bt_text = str(ship.breakthrough)
            bt_item = QTableWidgetItem(bt_text)
            bt_item.setTextAlignment(Qt.AlignCenter)
            bt_item.setData(Qt.UserRole, ship.breakthrough)
            self.setItem(row, 4, bt_item)

            oath_item = QTableWidgetItem("❤" if ship.oath else "✗")
            oath_item.setTextAlignment(Qt.AlignCenter)
            oath_item.setData(Qt.UserRole, ship.oath)  # 存储布尔值用于排序
            self.setItem(row, 5, oath_item)

            level120_item = QTableWidgetItem("✓" if ship.level_120 else "✗")
            level120_item.setTextAlignment(Qt.AlignCenter)
            level120_item.setData(Qt.UserRole, ship.level_120)
            self.setItem(row, 6, level120_item)

        # 默认选中第一行
        if ships:
            self.selectRow(0)

        #self.itemSelectionChanged.connect(self.on_selection_changed)
        
    def update_ship(self, ship):
        # 临时断开 selection 信号，避免循环
        #self.itemSelectionChanged.disconnect(self.on_selection_changed)
        for row, s in enumerate(self.current_ships):
            if s.id == ship.id:
                # 更新 current_ships 中的对象引用
                self.current_ships[row] = ship
                # 更新表格显示
                self.item(row, 1).setText(str(ship.id))
                display_name = ship.name
                if ship.alt_name:
                    display_name = f"{ship.name}（{ship.alt_name}）"
                name_item = QTableWidgetItem(display_name)
                name_item.setToolTip(ship.name)
                if ship.special_gear_name:
                    name_item.setToolTip(f"特殊兵装: {ship.special_gear_name}")
                name_item.setToolTip(ship.name)
                self.setItem(row, 2, name_item)
                self.item(row, 3).setText("✓" if ship.owned else "✗")
                bt_text = "满破" if ship.breakthrough == 3 else str(ship.breakthrough)
                self.item(row, 4).setText(bt_text)
                self.item(row, 4).setData(Qt.UserRole, ship.breakthrough)
                self.item(row, 5).setText("❤" if ship.oath else "✗")
                self.item(row, 5).setData(Qt.UserRole, ship.oath)
                self.item(row, 6).setText("✓" if ship.level_120 else "✗")
                self.item(row, 6).setData(Qt.UserRole, ship.level_120)
                # 如果当前选中的就是这一行，可以更新详情（但为避免循环，通常不需要）
                break

        # 重新连接信号
        #self.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        row = self.currentRow()
        if 0 <= row < len(self.current_ships):
            #self.current_ship_changed.emit(self.current_ships[row])
            self._pending_row = row
            self.selection_timer.start(50)
        else:
            self._pending_row = None
            self.selection_timer.stop()
            self.current_ship_changed.emit(None)

    def on_sort_indicator_changed(self, logicalIndex, order):
        # 根据列索引确定排序字段
        key_map = {0: "id", 1: "name", 3: "rarity", 4: "oath", 5: "level120"}  # 突破列也可以排序，但这里简化
        if logicalIndex in key_map:
            reverse = (order == Qt.DescendingOrder)
            self.sort_requested.emit(key_map[logicalIndex], reverse)

    def get_current_ship(self):
        row = self.currentRow()
        if 0 <= row < len(self.current_ships):
            return self.current_ships[row]
        return None

    def show_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        ship = self.current_ships[row]
        menu = QMenu(self)

        # 标记为已获得/未获得
        action_owned = menu.addAction("标记为已获得" if not ship.owned else "标记为未获得")
        action_owned.triggered.connect(lambda: self.mark_owned_requested.emit(ship.id, not ship.owned))

        # 标记为已满破/未满破
        action_max = menu.addAction("标记为已满破" if not ship.is_max_breakthrough() else "标记为未满破")
        action_max.triggered.connect(lambda: self.mark_max_breakthrough_requested.emit(ship.id, not ship.is_max_breakthrough()))

        # 标记为已120/未120
        action_120 = menu.addAction("标记为已120" if not ship.level_120 else "标记为未120")
        action_120.triggered.connect(lambda: self.mark_level120_requested.emit(ship.id, not ship.level_120))

        # 标记为已誓约/未誓约
        action_oath = menu.addAction("标记为已誓约" if not ship.oath else "标记为未誓约")
        action_oath.triggered.connect(lambda: self.mark_oath_requested.emit(ship.id, not ship.oath))

        # 删除舰船（仅开发模式）
        if self.dev_mode and self.account_manager and self.account_manager.is_developer():
            menu.addSeparator()
            action_delete = menu.addAction("删除舰船")
            action_delete.triggered.connect(lambda: self.delete_ship_requested.emit(ship.id))

        menu.exec(self.viewport().mapToGlobal(pos))

    def get_checked_ship_ids(self):
        ids = []
        for row in range(self.rowCount()):
            if self.item(row, 0).checkState() == Qt.Checked:
                ids.append(self.current_ships[row].id)
        return ids
    
    def clear_checks(self):
        """清空所有复选框的勾选状态"""
        for row in range(self.rowCount()):
            self.item(row, 0).setCheckState(Qt.Unchecked)

    def on_current_item_changed(self, current, previous):
        # 每次当前项改变时，启动延迟定时器
        self.current_item_timer.start(50)  # 50ms 后发射最终选择

    def _delayed_current_item_changed(self):
        # 获取当前选中的项
        current = self.currentItem()
        if current:
            row = current.row()
            if 0 <= row < len(self.current_ships):
                self.current_ship_changed.emit(self.current_ships[row])
            else:
                self.current_ship_changed.emit(None)
        else:
            self.current_ship_changed.emit(None)