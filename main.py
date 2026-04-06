import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from gui.main_window import MainWindow
from PySide6.QtGui import QFont, QFontDatabase, QIcon

def resource_path(relative_path):
    """获取资源文件的绝对路径（兼容开发环境和打包后的环境）"""
    try:
        # PyInstaller/Nuitka 打包后临时目录
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境：当前文件所在目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

image_dir = resource_path("images")
ship_json = resource_path("ships.json")

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("app_icon.ico")))
    #app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    #app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setAttribute(Qt.AA_SynthesizeTouchForUnhandledMouseEvents, True)
    
    # 在创建 app 后，加载字体
    font_id = QFontDatabase.addApplicationFont("font/MiSansVF_4.009.ttf")
    #print("主界面全局字体ID:", font_id)
    if font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            font = QFont()
            font.setFamilies(["Microsoft YaHei", "SimHei", "Source Han Sans SC", "Arial"])
            font.setPointSize(10)
            app.setFont(font)

    #app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()