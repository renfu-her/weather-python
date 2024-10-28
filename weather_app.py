import sys
import os
from dotenv import load_dotenv
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QComboBox, QPushButton, QLabel, QGridLayout,
                            QSystemTrayIcon, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction, QPixmap
import darkdetect  # 用於檢測系統主題

# 載入 .env 文件
load_dotenv()

class WeatherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("天氣小工具")
        self.setGeometry(1200, 100, 300, 200)
        
        # 設置窗口樣式為 Windows 原生樣式
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.MSWindowsFixedSizeDialogHint  # Windows 固定大小風格
        )
        
        # 天氣代碼對應的圖標
        self.weather_icons = {
            # 晴天
            "1": "sunny.png",
            # 多雲
            "4": "cloudy.png",
            # 晴時多雲
            "3": "partly_cloudy.png",
            # 陰天
            "7": "overcast.png",
            # 陰短暫雨
            "11": "rain.png",
            # 陰時多雲
            "6": "mostly_cloudy.png"
        }
        
        # 從環境變數獲取 API 金鑰
        self.api_key = os.getenv('CWA_API_KEY')
        if not self.api_key:
            raise ValueError("找不到 API 金鑰，請確認 .env 文件設置正確")
        
        self.setup_ui()
        self.setup_system_tray()
        self.apply_theme()
        
        # 設置自動更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.get_weather)
        self.timer.start(1800000)  # 30分鐘更新一次
        
        self.get_weather()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 地區選擇
        location_layout = QVBoxLayout()
        self.location_label = QLabel("選擇地區")
        self.location_combo = QComboBox()
        
        # 地區列表（按區域排序）
        north = ["臺北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "宜蘭縣"]
        central = ["苗栗縣", "臺中市", "彰化縣", "南投縣", "雲林縣"]
        south = ["嘉義縣", "嘉義市", "臺南市", "高雄市", "屏東縣"]
        east = ["花蓮縣", "臺東縣"]
        islands = ["澎湖縣", "金門縣", "連江縣"]
        
        self.locations = north + central + south + east + islands
        self.location_combo.addItems(self.locations)
        location_layout.addWidget(self.location_label)
        location_layout.addWidget(self.location_combo)
        
        # 更新按鈕
        self.query_btn = QPushButton("更新天氣")
        self.query_btn.clicked.connect(self.get_weather)
        self.query_btn.setFixedHeight(32)
        
        # 天氣圖標顯示
        self.weather_icon_label = QLabel()
        self.weather_icon_label.setFixedSize(64, 64)  # 設置圖標大小
        
        # 天氣信息顯示
        self.weather_display = QLabel()
        self.weather_display.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 創建水平布局來放置圖標和天氣信息
        weather_layout = QHBoxLayout()
        weather_layout.addWidget(self.weather_icon_label)
        weather_layout.addWidget(self.weather_display)
        weather_layout.addStretch()
        
        # 添加到主布局
        layout.addLayout(location_layout)
        layout.addWidget(self.query_btn)
        layout.addLayout(weather_layout)

    def apply_theme(self):
        # 檢測系統主題
        is_dark = darkdetect.isDark()
        
        if is_dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #202020;
            }
            QWidget {
                background-color: #202020;
                color: #ffffff;
            }
            QComboBox {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow_white.png);
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1984d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QLabel {
                color: #ffffff;
                padding: 2px;
            }
        """)

    def apply_light_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QWidget {
                background-color: #f0f0f0;
                color: #000000;
            }
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 5px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow_black.png);
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1984d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QLabel {
                color: #000000;
                padding: 2px;
            }
        """)

    def setup_system_tray(self):
        """設置系統托盤"""
        # 創建系統托盤圖標
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icons/app_icon.png"))
        self.tray_icon.setToolTip("天氣小工具")  # 懸停提示文字
        
        # 創建托盤菜單
        self.tray_menu = QMenu()
        
        # 添加菜單項
        self.show_action = QAction("顯示", self)
        self.show_action.triggered.connect(self.show_window)
        
        self.hide_action = QAction("隱藏", self)
        self.hide_action.triggered.connect(self.hide_window)
        
        self.refresh_action = QAction("更新天氣", self)
        self.refresh_action.triggered.connect(self.get_weather)
        
        self.quit_action = QAction("退出", self)
        self.quit_action.triggered.connect(self.quit_application)
        
        # 添加分隔線和菜單項
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.hide_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.refresh_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.quit_action)
        
        # 設置托盤圖標的菜單
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 連接托盤圖標的點擊事件
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 顯示托盤圖標
        self.tray_icon.show()
        
        # 更新菜單項狀態
        self.update_menu_state()

    def tray_icon_activated(self, reason):
        """處理托盤圖標的點擊事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 單擊
            if self.isVisible():
                self.hide_window()
            else:
                self.show_window()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:  # 雙擊
            self.show_window()

    def show_window(self):
        """顯示窗口"""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()  # 激活窗口
        self.update_menu_state()
        
        # 更新天氣信息
        self.get_weather()

    def hide_window(self):
        """隱藏窗口"""
        self.hide()
        self.update_menu_state()
        
        # 修正: 使用正確的圖標枚舉
        self.tray_icon.showMessage(
            "天氣小工具",
            "應用程序已最小化到系統托盤",
            QSystemTrayIcon.MessageIcon.Information,  # 修改這裡
            2000
        )

    def update_menu_state(self):
        """更新菜單項的狀態"""
        is_visible = self.isVisible()
        self.show_action.setEnabled(not is_visible)
        self.hide_action.setEnabled(is_visible)

    def closeEvent(self, event):
        """處理窗口關閉事件"""
        if self.tray_icon.isVisible():
            event.ignore()
            self.hide_window()
        else:
            event.accept()

    def quit_application(self):
        """完全退出應用程序"""
        reply = QMessageBox.question(
            self,
            '確認退出',
            '確定要退出程式嗎？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 保存任何需要的數據
            # ...
            
            # 移除托盤圖標
            self.tray_icon.hide()
            
            # 退出應用程序
            QApplication.quit()

    def update_tray_tooltip(self, weather_info):
        """更新托盤圖標的提示信息"""
        try:
            location = self.location_combo.currentText()
            wx = weather_info.get('weather', '')
            temp = weather_info.get('temperature', '')
            self.tray_icon.setToolTip(f"{location}: {wx}\n溫度: {temp}")
        except Exception as e:
            print(f"更新托盤提示失敗: {str(e)}")

    def get_weather(self):
        location = self.location_combo.currentText()
        url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
        params = {
            "Authorization": self.api_key,
            "locationName": location
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["success"] == "true":
                location_data = data["records"]["location"][0]
                
                # 獲取天氣數據
                wx_data = location_data["weatherElement"][0]["time"][0]["parameter"]
                wx = wx_data["parameterName"]
                wx_code = wx_data["parameterValue"]
                
                min_t = location_data["weatherElement"][2]["time"][0]["parameter"]["parameterName"]
                max_t = location_data["weatherElement"][4]["time"][0]["parameter"]["parameterName"]
                pop = location_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
                ci = location_data["weatherElement"][3]["time"][0]["parameter"]["parameterName"]
                
                # 更新天氣圖標
                if wx_code in self.weather_icons:
                    icon_path = f"icons/{self.weather_icons[wx_code]}"
                    pixmap = QPixmap(icon_path)
                    scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, 
                                                Qt.TransformationMode.SmoothTransformation)
                    self.weather_icon_label.setPixmap(scaled_pixmap)
                
                # 格式化顯示文本
                weather_text = (
                    f"地區：{location}\n"
                    f"天氣：{wx}\n"
                    f"溫度：{min_t}°C - {max_t}°C\n"
                    f"降雨機率：{pop}%\n"
                    f"體感：{ci}"
                )
                
                self.weather_display.setText(weather_text)
                self.tray_icon.setToolTip(f"{location}: {wx} {min_t}°C-{max_t}°C")
                
        except Exception as e:
            self.weather_display.setText(f"獲取天氣信息失敗: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 設置應用程序不會在最後一個窗口關閉時退出
    app.setQuitOnLastWindowClosed(False)
    
    # 設置應用程序圖標
    app_icon = QIcon("icons/app_icon.png")
    app.setWindowIcon(app_icon)
    
    # 使用 Windows 原生風格
    app.setStyle('Windows')
    
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())
