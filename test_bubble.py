#!/usr/bin/env python
"""
测试桌宠气泡显示功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import QTimer
from modeling.desktop_pet import PetRenderer

class BubbleTestWindow(QWidget):
    """测试气泡显示的简单窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("气泡显示测试")
        self.setGeometry(100, 100, 400, 400)

        # 创建PetRenderer实例
        self.renderer = PetRenderer(self)
        self.renderer.setFixedSize(300, 400)

        layout = QVBoxLayout()

        # 测试按钮
        self.btn_show = QPushButton("显示气泡")
        self.btn_show.clicked.connect(self.show_bubble)

        self.btn_hide = QPushButton("隐藏气泡")
        self.btn_hide.clicked.connect(self.hide_bubble)

        self.btn_test_text = QPushButton("测试短文本")
        self.btn_test_text.clicked.connect(lambda: self.show_test_text("你好！"))

        self.btn_test_long = QPushButton("测试长文本")
        self.btn_test_long.clicked.connect(lambda: self.show_test_text(
            "这是一个较长的测试文本，用于验证气泡的自适应换行功能。气泡应该能够自动调整大小以适应文本内容。"
        ))

        layout.addWidget(self.btn_show)
        layout.addWidget(self.btn_hide)
        layout.addWidget(self.btn_test_text)
        layout.addWidget(self.btn_test_long)
        layout.addWidget(self.renderer)

        self.setLayout(layout)

        # 自动关闭定时器
        QTimer.singleShot(30000, self.close)  # 30秒后自动关闭

    def show_bubble(self):
        """显示测试气泡"""
        self.renderer.show_bubblele("测试气泡显示！", timeout_ms=3000)

    def hide_bubble(self):
        """隐藏气泡"""
        self.renderer.hide_bubblele()

    def show_test_text(self, text):
        """显示指定文本"""
        self.renderer.show_bubblele(text, timeout_ms=5000)

def main():
    app = QApplication(sys.argv)
    window = BubbleTestWindow()
    window.show()

    # 启动后自动显示一个测试气泡
    QTimer.singleShot(1000, window.show_bubble)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()