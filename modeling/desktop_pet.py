# Nakari Desktop Pet
import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap, QIcon

class PetRenderer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expr = 'neutral'
        self.target_expr = 'neutral'
        self.mouth_val = 0.0
        self.is_speaking = False
        self.float_y = 0.0
        self.float_dir = 1
        self.dragging = False
        self.drag_pos = QPoint()
        self.blinking = False

        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(30)

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(4000)

    def animate(self):
        if self.expr != self.target_expr:
            self.expr = self.target_expr
        self.update()

        self.float_y += 0.002 * self.float_dir
        if abs(self.float_y) > 2:
            self.float_dir *= -1

    def blink(self):
        self.blinking = True
        self.update()
        QTimer.singleShot(120, lambda: setattr(self, 'blinking', False) or self.update())
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
        self.mouth_val = 0.0
        self.update()

    def speak_anim(self):
        import random
        self.mouth_val = random.random() * 0.7 + 0.2
        self.update()

    def paintEvent(self, event):
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

        if self.blinking:
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
            mouth_open = int(self.mouth_val * 12)
            painter.drawEllipse(int(w*0.44), mouth_y - 2, int(w*0.12), int(eye_h*0.22) + mouth_open)
        else:
            painter.setBrush(QColor(215, 105, 125))
            mouth_open = int(self.mouth_val * 10) if self.is_speaking else 0
            if mouth_open > 2:
                painter.drawEllipse(int(w*0.45), mouth_y, int(w*0.1), int(eye_h*0.15) + mouth_open)
            else:
                painter.drawEllipse(int(w*0.46), mouth_y + 2, int(w*0.08), int(eye_h*0.08))

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
        expressions = ['neutral', 'happy', 'sad', 'surprised', 'thinking']
        idx = (expressions.index(self.target_expr) + 1) % len(expressions)
        self.set_expression(expressions[idx])


class DesktopPetWindow(QWidget):
    def __init__(self):
        super().__init__()
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

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
