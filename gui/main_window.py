import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                                QSplitter, QMessageBox, QFileDialog, QApplication, QPushButton, QDialog, QLabel)
from PySide6.QtCore import Qt, QSettings, QPoint, QPropertyAnimation, QEasingCurve, Signal, QUrl, QTimer
from PySide6.QtGui import QFont, QIcon, QPainter, QBrush, QPen, QColor, QLinearGradient, QPalette, QPixmap, QDesktopServices

import ctypes
from ctypes import wintypes

from manager import ShipManager
from gui.filter_bar import FilterBar
from gui.ship_list_widget import ShipListWidget
from gui.detail_widget import DetailWidget
from gui.stat_dialog import StatDialog
from gui.add_ship_dialog import AddShipDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("碧蓝航线本地图鉴")
        self.resize(1300, 700)
        self.setMinimumWidth(800)

        # 移除默认标题栏
        #self.setWindowFlags(Qt.FramelessWindowHint)
        # 允许透明背景（用于圆角）
        #self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置调色板透明
        #palette = self.palette()
        #palette.setColor(QPalette.Window, QColor(0, 0, 0, 0))  # 完全透明
        #self.setPalette(palette)

        # 创建中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 主布局
        #main_layout = QVBoxLayout(central)
        #main_layout.setContentsMargins(10, 10, 10, 10)  # 留出阴影空间
        #main_layout.setSpacing(0)

        # ---- 自定义标题栏 ----
        #self.title_bar = QWidget()
        #self.title_bar.setFixedHeight(40)
        #self.title_bar.setObjectName("titleBar")
        #title_layout = QHBoxLayout(self.title_bar)
        #title_layout.setContentsMargins(10, 0, 10, 0)

        # 图标和标题
        #self.icon_label = QLabel()
        #self.icon_label.setPixmap(QPixmap("ald.ico").scaled(20,20))
        #title_layout.addWidget(self.icon_label)

        #self.title_label = QLabel("碧蓝航线本地图鉴")
        #self.title_label.setStyleSheet("color: #f0f0f0; font-weight: bold;")
        #title_layout.addWidget(self.title_label)
        #title_layout.addStretch()

        # 窗口控制按钮
        #self.min_btn = QPushButton("－")
        #self.max_btn = QPushButton("□")
        #self.close_btn = QPushButton("×")
        #for btn in (self.min_btn, self.max_btn, self.close_btn):
        #    btn.setFixedSize(40, 30)
        #    btn.setFocusPolicy(Qt.NoFocus)
        #    btn.setObjectName("titleButton")
        #self.min_btn.clicked.connect(self.showMinimized)
        #self.max_btn.clicked.connect(self.toggle_maximize)
        #self.close_btn.clicked.connect(self.close)

        #title_layout.addWidget(self.min_btn)
        #title_layout.addWidget(self.max_btn)
        #title_layout.addWidget(self.close_btn)

        #main_layout.addWidget(self.title_bar)
        #main_layout.addWidget(self.title_bar, 0)  # 固定高度
        #main_layout.addWidget(content_widget)
        #main_layout.addWidget(content_widget, 1)  # 拉伸因子
        #main_layout.setStretchFactor(content_widget, 1)

        # 加载样式表
        #with open("gui/style.qss", "r", encoding='utf-8') as f:
        #    self.setStyleSheet(f.read())

        # ---- 内容区域（原有的所有控件） ----
        #content_widget = QWidget()
        #content_layout = QVBoxLayout(content_widget)
        #content_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部工具栏布局（包含筛选栏和主题切换按钮）
        top_layout = QHBoxLayout()
        self.filter_bar = FilterBar()
        self.filter_bar.fleet_tech_clicked.connect(self.show_fleet_tech)
        self.filter_bar.theme_toggled.connect(self.toggle_theme)
        top_layout.addWidget(self.filter_bar)

        # 舰队科技
        #self.fleet_tech_btn = QPushButton("舰队科技")
        #self.fleet_tech_btn.clicked.connect(self.show_fleet_tech)
        #top_layout.addWidget(self.fleet_tech_btn)
        
        # 主题切换按钮
        #self.theme_btn = QPushButton("切换主题")
        #self.theme_btn.clicked.connect(self.toggle_theme)
        #top_layout.addWidget(self.theme_btn)

        main_layout.addLayout(top_layout)

        # 中间分割区域
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(0)
        self.splitter.setChildrenCollapsible(False)
        main_layout.addWidget(self.splitter, 1)  # 拉伸因子1

        # 左侧列表
        self.ship_list = ShipListWidget()
        self.splitter.addWidget(self.ship_list)

        # 右侧详情
        self.detail_widget = DetailWidget()
        self.detail_widget.main_window = self
        self.splitter.addWidget(self.detail_widget)

        # 设置初始比例
        self.splitter.setSizes([400, 900])
        #self.splitter.setHandleWidth(int)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(12)

        # 连接信号
        self.filter_bar.filter_changed.connect(self.apply_filter)
        self.filter_bar.reset_clicked.connect(self.reset_filter)
        self.filter_bar.stat_clicked.connect(self.show_stat_dialog)
        self.filter_bar.add_ship_clicked.connect(self.show_add_ship_dialog)
        self.filter_bar.switch_file_clicked.connect(self.switch_file)
        self.filter_bar.export_clicked.connect(self.export_data)
        self.filter_bar.import_clicked.connect(self.import_data)
        self.filter_bar.update_online_clicked.connect(self.update_online)
        self.filter_bar.sort_order_changed.connect(self.on_sort_order_changed)
        self.filter_bar.batch_operation_signal.connect(self.batch_operation)

        self.filter_bar.main_window = self

        self.ship_list.current_ship_changed.connect(self.on_ship_selected)
        self.ship_list.sort_requested.connect(self.on_sort_requested)

        self.detail_widget.data_changed.connect(self.on_ship_updated)
        
        #main_layout.addWidget(content_widget)
        self.setMinimumSize(200, 200)
        self.ship_list.setMinimumWidth(0)
        self.detail_widget.setMinimumWidth(0)

        # 初始化设置存储（使用公司名和应用名，可自定义）
        self.settings = QSettings("菲梦林光", "AzurLaneDex")
        # 初始化数据管理器
        self.manager = ShipManager("ships.json")
        self.filter_bar.manager = self.manager
        ship_names = [ship.name for ship in self.manager.ships]
        self.filter_bar.set_ship_names(ship_names)

        #self.system_follow = (self.manager.config.get("theme_mode", "system") == "system")
        theme_mode = self.manager.config.get("theme_mode", "system")
        self.system_follow = (theme_mode == "system")
        if self.system_follow:
            app = QApplication.instance()
            if hasattr(app.styleHints(), 'colorScheme'):
                current_scheme = app.styleHints().colorScheme()
                if current_scheme == Qt.ColorScheme.Dark:
                    self.manager.current_theme = "dark"
                else:
                    self.manager.current_theme = "light"
            else:
                # 对于 Qt < 6.5，需要其他方法获取，例如读取注册表
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    self.manager.current_theme = "dark" if value == 0 else "light"
                except:
                    self.manager.current_theme = "light"  # 默认
            self.load_theme()
        else:
            self.manager.current_theme = theme_mode
            self.load_theme()
        #self.current_manual_theme = self.manager.config.get("manual_theme", "light")
        #self.apply_theme()
        #self.load_theme()
        self.setup_theme_monitor()

        # 初始加载全部舰船
        self.apply_filter({})

    def show_fleet_tech(self):
        camp_tech = self.manager.calculate_camp_tech_points()
        global_bonuses = self.manager.calculate_global_bonuses()
        from gui.fleet_tech_dialog import FleetTechDialog
        dlg = FleetTechDialog(camp_tech, global_bonuses, self)
        dlg.exec()
        
    def load_theme(self):
        """加载保存的主题，并将样式表应用到整个应用"""
        #theme = self.settings.value("theme", "light")  # 默认浅色
        theme = self.manager.current_theme
        #print(f"应用主题: {theme}")
        style_file = f"style_{theme}.qss"
        # 获取当前文件所在目录的绝对路径
        base_dir = os.path.dirname(__file__)
        style_path = os.path.join(base_dir, style_file)
        #print(f"Loading theme: {theme}, path: {style_path}") #1
        if os.path.exists(style_path):
            with open(style_path, "r", encoding='utf-8') as f:
                qss = f.read() #2
                #print(f"QSS content length: {len(qss)}") #3
                #print(f"QSS preview: {qss[:200]}") #4
                QApplication.instance().setStyleSheet(f.read())
            app = QApplication.instance()
            app.setStyleSheet(qss)
                # 强制所有顶级窗口重新应用样式
            for widget in app.topLevelWidgets():
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
                app.processEvents()
        else:
            print(f"样式文件不存在: {style_path}")

    def toggle_theme(self):
        """切换深色/浅色主题"""
        current = self.settings.value("theme", "light")
        new_theme = "dark" if current == "light" else "light"
        self.settings.setValue("theme", new_theme)
        self.load_theme()
        # 强制刷新界面
        self.repaint()

    def apply_filter(self, criteria):
        print(f"筛选条件: {criteria}")
        filtered = self.manager.filter(criteria)
        # 排序（默认按编号）
        #print(f"筛选后舰船数: {len(filtered)}")
        filtered = self.manager.sort(filtered, key="id")
        self.ship_list.set_ships(filtered)
        if filtered:
            self.ship_list.selectRow(0)   # 默认选中第一项
        else:
            self.detail_widget.clear()

    def reset_filter(self):
        self.filter_bar.reset()
        self.apply_filter({})

    def on_ship_selected(self, ship):
        #print(f"on_ship_selected: ship = {ship}")
        if ship:
            self.detail_widget.set_ship(ship)
        else:
            self.detail_widget.clear()
        
    def on_ship_updated(self, ship):
        # 更新数据管理器中的对应船
        for i, s in enumerate(self.manager.ships):
            if s.id == ship.id:
                self.manager.ships[i] = ship
                break
        self.manager.save()
        # 刷新左侧列表显示
        self.ship_list.update_ship(ship)
        self.apply_filter(self.filter_bar.get_criteria())
        if self.ship_list.currentRow() >= 0 and self.ship_list.current_ships[self.ship_list.currentRow()].id == ship.id:
            self.detail_widget.set_ship(ship)
        #if ship:
        #    print(f"Selected ship: {ship.id}, owned={ship.owned}, oath={ship.oath}, level120={ship.level_120}")
        #    self.detail_widget.set_ship(ship)
        #else:
        #    self.detail_widget.clear()

        # 连接信号（确保在创建 detail_widget 之后）
        #self.detail_widget.data_changed.connect(self.on_ship_updated)

    def on_sort_requested(self, key, reverse):
        filtered = self.ship_list.current_ships  # 当前显示的列表
        sorted_ships = self.manager.sort(filtered, key, reverse)
        self.ship_list.set_ships(sorted_ships)

    def show_stat_dialog(self):
        stats_dict = self.manager.stats()
        dlg = StatDialog(stats_dict, self)
        dlg.exec()

    def show_add_ship_dialog(self):
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
            self.filter_bar.set_ship_names(ship_names)
            print("已调用 manager.add_ship")
            # 刷新列表（可能需要重新应用当前筛选）
            self.apply_filter(self.filter_bar.get_criteria())
        else:
            print("用户取消")

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

    def update_online(self):
        reply = QMessageBox.question(
            self,
            "检查更新",
            "是否检查程序新版本？\n\n注意：数据更新会同时进行，您可以选择跳过程序更新。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
    
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            # 检查程序版本
            latest_version = self.manager.get_latest_version()
            current_version = "1.0.0"  # 请将当前版本硬编码或从配置文件读取
            if latest_version and latest_version > current_version:
                ret = QMessageBox.question(
                    self,
                    "发现新版本",
                    f"发现新版本 {latest_version}（当前 {current_version}）\n\n是否前往下载页面？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if ret == QMessageBox.Yes:
                    QDesktopServices.openUrl(QUrl("https://github.com/xiwangzaiqianfang/AzurLane-Dex/releases/latest"))
            else:
                QMessageBox.information(self, "检查更新", "当前已是最新版本。")
        
            """从网络更新数据"""
            # 可以弹出一个对话框让用户输入 URL，或者使用固定的默认 URL
            default_url = "https://raw.githubusercontent.com/xiwangzaiqianfang/AzurLane-Dex/main/ships.json"
            success = self.manager.update_from_github(default_url)
            if success:
                self.apply_filter(self.filter_bar.get_criteria())
                QMessageBox.information(self, "完成", "数据更新成功！")
            else:
                QMessageBox.information(self, "无需更新", "数据已是最新版本。")
            # 简单的确认对话框
            #reply = QMessageBox.question(
            #    self, 
            #    "确认更新", 
            #    f"将从以下地址更新数据：\n{default_url}\n\n您的当前状态（拥有、突破等）会被保留，是否继续？",
            #    QMessageBox.Yes | QMessageBox.No
            #)
        #if reply == QMessageBox.No:
        #    return
        #try:
        #    QApplication.setOverrideCursor(Qt.WaitCursor)
        #    success = self.manager.update_from_github(default_url)
        #    if success:
        #        ship_names = [ship.name for ship in self.manager.ships]
        #        self.filter_bar.set_ship_names(ship_names)
        #        self.apply_filter(self.filter_bar.get_criteria())
        #        QMessageBox.information(self, "完成", "数据更新成功！")
        #    else:
        #        QMessageBox.information(self, "无需更新", "当前已是最新版本。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败：{str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

    def closeEvent(self, event):
        """窗口关闭时保存大小和位置"""
        self.settings.setValue("window_geometry", self.saveGeometry())
        super().closeEvent(event)

    def showEvent(self, event):
        """窗口显示时恢复上次的大小和位置"""
        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        super().showEvent(event)

    def get_current_ship(self):
        #print("====DEBUG====")
        #print("main_window.get_current_ship 被调用")
        ship = self.ship_list.get_current_ship()
        #print(f"从 ship_list 获取到的 ship: {ship}")
        return ship

    def on_sort_order_changed(self, key, reverse):
        """用户改变排序方式时，重新排序当前列表"""
        # 获取当前显示的舰船列表（即已经过筛选的列表）
        current_ships = self.ship_list.current_ships
        sorted_ships = self.manager.sort(current_ships, key, reverse)
        self.ship_list.set_ships(sorted_ships)
        # 注意：由于排序改变了列表顺序，但筛选条件未变，我们不需要重新应用筛选。
        # 同时，当前选中的船可能改变，但 set_ships 会自动选中第一行。

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

        self.manager.save()
        if checked_ids:
            self.ship_list.clear_checks()
        # 刷新界面：重新应用筛选（列表更新）并刷新详情页
        self.apply_filter(self.filter_bar.get_criteria())
        QMessageBox.information(self, "完成", f"已批量修改 {len(ships_to_modify)} 艘舰船。")

    def setup_theme_monitor(self):
        if hasattr(QApplication.instance().styleHints(), 'colorSchemeChanged'):
            # Qt 6.5+ 支持信号
            QApplication.instance().styleHints().colorSchemeChanged.connect(self.on_system_theme_changed)
        else:
            # 低版本 Qt，使用定时器轮询（简单实现）
            self.theme_timer = QTimer(self)
            self.theme_timer.timeout.connect(self.check_system_theme)
            self.theme_timer.start(2000)

    def check_system_theme(self):
        # 简化：读取注册表或判断 Windows 10/11 当前主题
        # 这里用简单方法：判断默认系统颜色，假设 Windows 10/11 深色模式注册表路径
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            system_dark = (value == 0)
        except:
            system_dark = False
        if self.system_follow:
            new_theme = "dark" if system_dark else "light"
            if new_theme != self.manager.version_theme:
                self.manager.version_theme = new_theme
                self.load_theme()

    def on_system_theme_changed(self, color_scheme):
        if self.system_follow:
            new_theme = "dark" if color_scheme == Qt.ColorScheme.Dark else "light"
            if new_theme != self.manager.current_theme:
                print(f"[主题] 系统主题变化，新主题: {new_theme}")
                self.manager.current_theme = new_theme
                self.load_theme()

    def set_system_theme_follow(self, follow):
        print(f"[主题] 跟随系统主题: {follow}")
        self.system_follow = follow
        if follow:
            # 立即根据当前系统主题切换
            app = QApplication.instance()
            if hasattr(app.styleHints(), 'colorScheme'):
                current_scheme = app.styleHints().colorScheme()
                new_theme = "dark" if current_scheme == Qt.ColorScheme.Dark else "light"
                self.manager.current_theme = new_theme
                self.load_theme()
            else:
                # 低版本 Qt 可读取注册表等
                # 这里简单默认浅色
                self.manager.current_theme = "light"
                self.load_theme()
            #self.on_system_theme_changed(QApplication.instance().styleHints().colorScheme())
        #else:
            # 手动模式，直接使用上次手动设置的主题
            #self.load_theme()

    def set_manual_theme(self, theme):
        print(f"[主题] 手动设置主题为: {theme}")
        self.system_follow = False
        self.manager.current_theme = theme
        #self.manager.config["manual_theme"] = theme
        #self.manager.save_config()
        self.load_theme()

    def open_settings(self):
        from gui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.manager, self)
        dlg.exec()

    def reset_window_geometry(self):
        """清除保存的窗口几何信息，并重置当前窗口到默认大小"""
        # 删除保存的几何信息
        self.settings.remove("window_geometry")
        # 重置当前窗口大小（默认 1200x800）
        self.resize(1300, 700)
        # 将窗口移动到屏幕中央
        self.center()

    def center(self):
        """将窗口移动到屏幕中央"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - self.rect().center())

    #def resizeEvent(self, event):
    #    super().resizeEvent(event)
    #    print(f"窗口尺寸: {self.width()} x {self.height()}")
    #    print(f"窗口最小宽度: {self.minimumWidth()}")
    #    print(f"左侧列表最小宽度: {self.ship_list.minimumWidth()}")
    #    print(f"右侧详情最小宽度: {self.detail_widget.minimumWidth()}")
    #    if hasattr(self, 'splitter'):
    #        sizes = self.splitter.sizes()
    #        print(f"分割器当前分配: {sizes[0]} / {sizes[1]}")
    #    else:
    #        print("splitter 不是实例变量")

    #def mousePressEvent(self, event):
    #    if event.button() == Qt.LeftButton and event.pos().y() <= self.title_bar.height():
    #        self.drag_pos = event.globalPosition().toPoint()
    #        event.accept()
    #    else:
    #        super().mousePressEvent(event)

    #def mouseMoveEvent(self, event):
    #    if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
    #        self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
    #        self.drag_pos = event.globalPosition().toPoint()
    #        event.accept()
    #    else:
    #        super().mouseMoveEvent(event)

    #def toggle_maximize(self):
    #    if self.isMaximized():
    #        self.showNormal()
    #        self.max_btn.setText("□")
            # 恢复圆角（通过样式表或代码）
    #        self.setStyleSheet(self.styleSheet() + "MainWindow { border-radius: 10px; }")
    #    else:
    #        self.showMaximized()
    #        self.max_btn.setText("❐")
            # 最大化时移除圆角
    #        self.setStyleSheet(self.styleSheet() + "MainWindow { border-radius: 0px; }")

    #def showEvent(self, event):
    #    super().showEvent(event)
    #    self.enable_acrylic()

    #def enable_acrylic(self):
    #    """启用 Windows 亚克力效果（适用于 Win10 1809+）"""
    #    try:
    #        import ctypes
    #        from ctypes import wintypes
    #        dwmapi = ctypes.windll.dwmapi
            # 亚克力效果属性
    #        DWMWA_USE_HOSTBACKDROPBRUSH = 37
    #        value = ctypes.c_int(1)
    #        hwnd = int(self.winId())
    #        dwmapi.DwmSetWindowAttribute(
    #            wintypes.HWND(hwnd),
    #            DWMWA_USE_HOSTBACKDROPBRUSH,
    #            ctypes.byref(value),
    #            ctypes.sizeof(value)
    #        )
    #        print("亚克力效果已启用")
    #    except Exception as e:
    #        print(f"亚克力效果不可用: {e}")