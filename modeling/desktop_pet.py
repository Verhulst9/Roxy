# Nakari Desktop Pet
import sys
import random
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu,
                                 QVBoxLayout, QLineEdit, QDialog)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap, QIcon


class ChatInputDialog(QDialog):
    """超简洁的对话输入框 - 只有输入行"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 扩大1.5倍尺寸
        self.setFixedSize(int(300 * 1.5), int(50 * 1.5))
        # 使用 Tool 窗口类型，非模态，允许父窗口交互
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # 透明背景容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
        """)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(20, 12, 20, 12)
        container_layout.setSpacing(0)
        container.setLayout(container_layout)

        # 只有输入框（字体也相应增大）
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("与 Nakari 对话...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: none;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                color: #333333;
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.95);
            }
        """)
        self.input_field.returnPressed.connect(self.accept)
        # 禁用输入框的右键菜单，让事件传递到对话框
        self.input_field.setContextMenuPolicy(Qt.NoContextMenu)

        # 启用整个对话框的右键菜单
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        container.setContextMenuPolicy(Qt.NoContextMenu)

        container_layout.addWidget(self.input_field)

        layout.addWidget(container)

    def position_below_parent(self):
        """将输入框定位到父窗口（桌宠）下方"""
        if self.parent():
            parent_geom = self.parent().geometry()
            # 计算位置：父窗口正下方，水平居中
            x = parent_geom.x() + (parent_geom.width() - self.width()) // 2
            y = parent_geom.y() + parent_geom.height() - 80  # 更紧密
            self.move(x, y)

    def contextMenuEvent(self, event):
        """右键点击任意位置关闭对话框"""
        self.close()
        event.accept()

    def mousePressEvent(self, event):
        """左键点击输入框外部时转发给父窗口用于拖动"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在输入框上
            input_rect = self.input_field.geometry()
            if not input_rect.contains(event.pos()):
                # 转发给父窗口处理拖动
                if self.parent():
                    self.parent().renderer.mousePressEvent(event)
            else:
                # 点击在输入框上，正常处理
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """移动事件转发给父窗口"""
        if self.parent():
            self.parent().renderer.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """释放事件转发给父窗口"""
        if self.parent():
            self.parent().renderer.mouseReleaseEvent(event)

    def get_input(self):
        """显示对话框并返回输入的文本"""
        if self.parent():
            self.position_below_parent()
        self.input_field.setFocus()
        self.show()
        # 非模态显示，让父窗口保持可交互


class PetRenderer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expr = 'neutral'
        self.target_expr = 'neutral'
        self.mouth_val_val = 0.0
        self.is_speaking = False
        self.float_y = 0.0
        self.float_dir = 1
        self.dragging = False
        self.drag_pos = QPoint()
        self.bblinking = False

        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(30)

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(4000)

        # 对话气泡
        self.bubblelelele_text = ""
        self.bubblelelele_visible = False
        self.bubblelelele_timer = QTimer()
        self.bubblelelele_timer.setSingleShot(True)
        self.bubblelelele_timer.timeout.connect(self.hide_bubblele)

    def animate(self):
        if self.expr != self.target_expr:
            self.expr = self.target_expr
        self.update()

        self.float_y += 0.002 * self.float_dir
        if abs(self.float_y) > 2:
            self.float_dir *= -1

    def blink(self):
        self.bblinking = True
        self.update()
        QTimer.singleShot(120, lambda: setattr(self, 'bblinking', False) or self.update())
        self.blink_timer.setInterval(random.randint(2500, 5000))

    def set_expression(self, expr):
        if expr in ['neutral', 'happy', 'sad', 'surprised', 'thinking']:
            self.target_expr = expr

    def speak_start(self):
        self.is_speaking = True
        self.speak_timer = QTimer()
        self.speak_timer.timeout.connect(self.speak_anim)
        self.speak_timer.start(100)

    def speak_stop(self):
        self.is_speaking = False
        if hasattr(self, 'speak_timer'):
            self.speak_timer.stop()
        self.mouth_val_val = 0.0
        self.update()

    def speak_anim(self):
        import random
        self.mouth_val_val = random.random() * 0.7 + 0.2
        self.update()

    def show_bubblele(self, text, timeout_ms=5000):
        """显示对话气泡，timeout_ms后自动隐藏"""
        self.bubblelelele_text = text
        self.bubblelelele_visible = True
        self.update()
        self.bubblelelele_timer.start(timeout_ms)

    def hide_bubblele(self):
        """隐藏对话气泡"""
        self.bubblelelele_visible = False
        self.bubblelelele_text = ""
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.translate(0, int(self.float_y))

        # Body
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 220, 235))
        painter.drawEllipse(int(w*0.28), int(h*0.38), int(w*0.44), int(h*0.35))

        # Head
        head_y = int(h*0.18)
        head_sz = int(h*0.26)
        painter.setBrush(QColor(255, 215, 230))
        painter.drawEllipse(int(w*0.32), head_y, int(w*0.36), head_sz)

        # Hair
        painter.setBrush(QColor(90, 75, 100))
        painter.drawEllipse(int(w*0.30), head_y - int(head_sz*0.1), int(w*0.40), int(head_sz*0.5))
        painter.drawEllipse(int(w*0.25), head_y + int(head_sz*0.12), int(w*0.12), int(head_sz*0.35))
        painter.drawEllipse(int(w*0.63), head_y + int(head_sz*0.12), int(w*0.12), int(head_sz*0.35))

        # Eyes
        eye_y = head_y + int(head_sz*0.25)
        eye_h = int(head_sz*0.12)

        if self.bblinking:
            painter.setPen(QPen(QColor(50, 50, 80), 3))
            painter.drawLine(int(w*0.38), eye_y + int(eye_h*0.5),
                       int(w*0.46), eye_y + int(eye_h*0.5))
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(60, 55, 80))
            painter.drawEllipse(int(w*0.38), eye_y, int(w*0.09), eye_h)
            painter.drawEllipse(int(w*0.54), eye_y, int(w*0.09), eye_h)

            # Highlights
            painter.setBrush(QColor(255, 255, 255, 220))
            painter.drawEllipse(int(w*0.405), eye_y + int(eye_h*0.2), int(w*0.025), int(eye_h*0.4))
            painter.drawEllipse(int(w*0.565), eye_y + int(eye_h*0.2), int(w*0.025), int(eye_h*0.4))

        # Brows
        brow_y = eye_y - int(eye_h*0.25)
        painter.setPen(QPen(QColor(75, 65, 90), 3))
        brow_off = 0
        if self.expr == 'sad':
            brow_off = 5
        elif self.expr == 'thinking':
            brow_off = -2
        painter.drawLine(int(w*0.37), brow_y + brow_off, int(w*0.41), brow_y - brow_off)
        painter.drawLine(int(w*0.54), brow_y + brow_off, int(w*0.58), brow_y - brow_off)

        # Blush
        blush_y = eye_y + int(eye_h*1.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 160, 190, 100))
        painter.drawEllipse(int(w*0.31), blush_y, int(w*0.15), int(eye_h*0.3))
        painter.drawEllipse(int(w*0.54), blush_y, int(w*0.15), int(eye_h*0.3))

        # Mouth
        mouth_y = blush_y + int(eye_h*0.5)
        painter.setPen(Qt.NoPen)

        if self.expr == 'happy':
            painter.setBrush(QColor(230, 110, 140))
            painter.drawChord(int(w*0.43), mouth_y, int(w*0.14), int(eye_h*0.2), 0, 180*16)
        elif self.expr == 'sad':
            painter.setBrush(QColor(210, 105, 125))
            painter.drawChord(int(w*0.43), mouth_y + 3, int(w*0.14), int(eye_h*0.15), 180*16, 360*16)
        elif self.expr == 'surprised':
            painter.setBrush(QColor(225, 100, 130))
            mouth_open = int(self.mouth_val_val * 12)
            painter.drawEllipse(int(w*0.44), mouth_y - 2, int(w*0.12), int(eye_h*0.22) + mouth_open)
        else:
            painter.setBrush(QColor(215, 105, 125))
            mouth_open = int(self.mouth_val_val * 10) if self.is_speaking else 0
            if mouth_open > 2:
                painter.drawEllipse(int(w*0.45), mouth_y, int(w*0.1), int(eye_h*0.15) + mouth_open)
            else:
                painter.drawEllipse(int(w*0.46), mouth_y + 2, int(w*0.08), int(eye_h*0.08))

        # 绘制对话气泡（美化版 - 右上角，自适应大小）
        if self.bubblelelele_visible and self.bubblelelele_text:
            from PyQt5.QtCore import QRectF
            from PyQt5.QtGui import QFont, QFontMetrics

            # 设置字体并计算文字大小
            # 提供字体回退机制
            font = QFont()
            font_families = ["Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "Arial", "Helvetica"]
            for font_family in font_families:
                font.setFamily(font_family)
                if font.exactMatch():  # 检查字体是否存在
                    break
            font.setPointSize(11)
            font.setBold(True)
            painter.setFont(font)

            font_metrics = QFontMetrics(font)

            # 计算文字所需的宽度和高度
            text_lines = self.bubblelelele_text.split('\n')
            max_line_width = 0
            total_height = 0

            padding_x = 24  # 左右内边距
            padding_y = 16  # 上下内边距
            line_spacing = 6  # 行间距

            for line in text_lines:
                # 使用horizontalAdvance()替代已弃用的width()方法，提供兼容性回退
                if hasattr(font_metrics, 'horizontalAdvance'):
                    line_width = font_metrics.horizontalAdvance(line)
                else:
                    line_width = font_metrics.width(line)  # 回退到旧方法
                max_line_width = max(max_line_width, line_width)
                total_height += font_metrics.height() + line_spacing

            # 限制最大宽度，防止气泡过宽
            max_bubblele_width = int(w * 0.7)
            min_bubblele_width = int(w * 0.25)

            # 如果文字过长，需要换行
            if max_line_width + padding_x * 2 > max_bubblele_width:
                # 重新计算换行后的高度
                available_width = max_bubblele_width - padding_x * 2
                wrapped_height = 0
                for line in text_lines:
                    # 估算每行需要的行数，提供兼容性回退
                    if hasattr(font_metrics, 'horizontalAdvance'):
                        line_width = font_metrics.horizontalAdvance(line)
                    else:
                        line_width = font_metrics.width(line)  # 回退到旧方法
                    lines_needed = max(1, (line_width + available_width - 1) // available_width)
                    wrapped_height += lines_needed * (font_metrics.height() + line_spacing)
                total_height = wrapped_height
                bubblele_w = max_bubblele_width
            else:
                bubblele_w = max(min_bubblele_width, max_line_width + padding_x * 2)

            bubblele_h = total_height + padding_y * 2

            # 气泡位置（桌宠右上方，不挡住桌宠）
            # 将气泡显示在窗口内部右侧，而不是外部
            bubblele_x = w - bubblele_w - 10  # 窗口内部右侧，距离右边框10px
            # 确保气泡不会超出窗口左侧边界
            if bubblele_x < 10:
                bubblele_x = 10
            bubblele_y = int(h * 0.05)  # 桌宠顶部靠上位置

            # 绘制阴影效果
            shadow_offset = 3
            shadow_rect = QRectF(bubblele_x + shadow_offset, bubblele_y + shadow_offset, bubblele_w, bubblele_h)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 30))  # 半透明阴影
            painter.drawRoundedRect(shadow_rect, 20, 20)

            # 绘制气泡主体（渐变粉色背景）
            bubblele_rect = QRectF(bubblele_x, bubblele_y, bubblele_w, bubblele_h)
            painter.setPen(QPen(QColor(255, 180, 200), 2))  # 粉色边框
            painter.setBrush(QColor(255, 245, 250, 250))  # 淡粉色背景
            painter.drawRoundedRect(bubblele_rect, 20, 20)  # 更圆润的圆角

            # 绘制小三角指向角色（从气泡左侧指向桌宠右上方）
            triangle_y = bubblele_y + int(bubblele_h * 0.4)
            triangle = [
                QPoint(bubblele_x, triangle_y),
                QPoint(bubblele_x - 10, triangle_y - 8),
                QPoint(bubblele_x - 3, triangle_y - 8)
            ]
            painter.setPen(QPen(QColor(255, 180, 200), 2))
            painter.setBrush(QColor(255, 245, 250, 250))
            painter.drawPolygon(*triangle)

            # 绘制文字（美化字体）
            painter.setPen(QColor(80, 60, 80))  # 深紫色文字

            # 绘制带内边距的文字（左对齐，自然换行）
            text_rect = QRectF(bubblele_x + padding_x, bubblele_y + padding_y // 2,
                            bubblele_w - padding_x * 2, bubblele_h - padding_y)
            painter.drawText(text_rect,
                           Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                           self.bubblelelele_text)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            if self.parent():
                self.drag_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.parent():
            self.parent().move(event.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event):
        # 双击直接打开对话
        if self.parent() and hasattr(self.parent(), 'chat_with_nakari'):
            self.parent().chat_with_nakari()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        menu.addAction("Happy", lambda: self.set_expression('happy'))
        menu.addAction("Sad", lambda: self.set_expression('sad'))
        menu.addAction("Thinking", lambda: self.set_expression('thinking'))
        menu.addSeparator()
        if self.parent() and hasattr(self.parent(), 'chat_with_nakari'):
            menu.addAction("对话...", self.parent().chat_with_nakari)
        menu.addSeparator()
        menu.addAction("Exit", self.parent_window_exit)

        menu.exec_(event.globalPos())

    def parent_window_exit(self):
        if self.parent():
            self.parent().close()


class DesktopPetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.chat_dialog = None  # 保存对话框引用
        self.init_ui()
        self.init_tray()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300, 400)

        self.renderer = PetRenderer(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.renderer)
        self.setLayout(layout)

        screen = QApplication.desktop().screenGeometry()
        self.move(screen.width() - 330, screen.height() - 480)

    def moveEvent(self, event):
        """窗口移动时，对话框跟随移动"""
        super().moveEvent(event)
        if self.chat_dialog and self.chat_dialog.isVisible():
            self.chat_dialog.position_below_parent()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(255, 180, 220))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))

        menu = QMenu()
        menu.addAction("Happy", lambda: self.renderer.set_expression('happy'))
        menu.addAction("Sad", lambda: self.renderer.set_expression('sad'))
        menu.addAction("Thinking", lambda: self.renderer.set_expression('thinking'))
        menu.addSeparator()
        menu.addAction("对话...", self.chat_with_nakari)
        menu.addSeparator()
        menu.addAction("Test Speech", self.test_speech)
        menu.addAction("Hide/Show", self.toggle_visible)
        menu.addSeparator()
        menu.addAction("Exit", self.close)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def test_speech(self):
        self.renderer.set_expression('happy')
        self.renderer.speak_start()
        QTimer.singleShot(2000, self.renderer.speak_stop)

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def chat_with_nakari(self):
        """与 Nakari 对话"""
        # 如果对话框已存在，先关闭
        if self.chat_dialog:
            self.chat_dialog.close()

        # 显示美化的输入对话框
        dialog = ChatInputDialog(self)
        self.chat_dialog = dialog
        dialog.input_field.returnPressed.disconnect()

        def on_submit():
            text = dialog.input_field.text().strip()
            dialog.close()
            self.chat_dialog = None  # 清除引用
            if text:
                # 显示思考状态
                self.renderer.set_expression('thinking')
                self.renderer.show_bubblele("正在思考...")

                try:
                    # 调用 API Server
                    response = requests.post(
                        "http://localhost:8000/api/chat",
                        json={"message": text, "session_id": "desktop_pet"},
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        reply = data.get("response", "")
                        # 显示回复
                        self.renderer.set_expression('happy')
                        self.renderer.speak_start()
                        self.renderer.show_bubblele(reply, timeout_ms=8000)
                        QTimer.singleShot(8000, self.renderer.speak_stop)
                    else:
                        self.renderer.set_expression('sad')
                        self.renderer.show_bubblele("抱歉，我暂时无法回应...")
                except Exception as e:
                    print(f"[Pet] Chat error: {e}")
                    self.renderer.set_expression('sad')
                    self.renderer.show_bubblele("连接失败，请检查 API Server")

        def on_close():
            self.chat_dialog = None  # 对话框关闭时清除引用

        dialog.input_field.returnPressed.connect(on_submit)
        dialog.finished.connect(on_close)
        dialog.get_input()

    def closeEvent(self, event):
        self.tray_icon.hide()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    pet = DesktopPetWindow()
    pet.show()

    sys.stdout.write("[Pet] Nakari Desktop Pet started!\n")
    sys.stdout.write("[Pet] Double-click to change expression\n")
    sys.stdout.write("[Pet] Drag to move\n")
    sys.stdout.write("[Pet] Right-click tray icon for menu\n")
    sys.stdout.write("[Pet] Right-click pet for action menu\n")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
