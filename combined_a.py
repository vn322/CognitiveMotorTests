# tests/combined_a.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
import time
import random
import math
from config import COLORS

class CombinedTestA(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.stimulus_time = None
        self.release_time = None
        self.click_time = None
        self.objects = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_positions)
        self.timeout_timer = None
        self.sample_shape = None
        self.sample_color = None
        self.click_pos = None
        self.button_rect = None

    def get_button_rect(self):
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 100, 160, 60)

    def paint(self, painter):
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        painter.setPen(COLORS['text'])
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)

        w = self.parent.width()
        h = self.parent.height()

        if self.state in ('waiting_start', 'holding'):
            self.draw_sample(painter)

        if self.state != 'finished':
            pressed = self.state in ('holding', 'stimulus_shown', 'moving')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                             "Запомните образец. Удерживайте «Старт», затем кликните на движущийся целевой стимул.")
        elif self.state in ('stimulus_shown', 'moving'):
            self.draw_objects(painter)

    def draw_sample(self, painter):
        sample_x, sample_y = 20, 20
        if self.state == 'waiting_start':
            self.sample_shape = random.choice(['circle', 'square'])
            self.sample_color = random.choice([
                QColor(255, 179, 186),  # red
                QColor(181, 234, 215),  # green
                QColor(255, 224, 179),  # yellow
                QColor(199, 206, 234)   # blue
            ])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.sample_color))
        size = 40
        rect = QRectF(sample_x, sample_y, size, size)
        if self.sample_shape == 'circle':
            painter.drawEllipse(rect)
        elif self.sample_shape == 'square':
            painter.drawRect(rect)

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn'].darker(120) if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Старт")

    def draw_objects(self, painter):
        for obj in self.objects:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(obj['color']))
            x, y = obj['pos'].x(), obj['pos'].y()
            size = 80
            rect = QRectF(x - size/2, y - size/2, size, size)
            if obj['shape'] == 'circle':
                painter.drawEllipse(rect)
            elif obj['shape'] == 'square':
                painter.drawRect(rect)

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.state = 'holding'
                self.button_rect = btn_rect
                self.parent.update()
                delay = random.uniform(0.5, 2.0)
                QTimer.singleShot(int(delay * 1000), self.show_stimuli)

    def mouseMoveEvent(self, event):
        if self.state in ('holding', 'stimulus_shown', 'moving') and self.button_rect:
            if not self.button_rect.contains(event.position()) and self.release_time is None:
                self.release_time = time.time()
                if self.state == 'holding':
                    self._emit_result(
                        latency=0,
                        motor_time=0,
                        total_rt=self.release_time - time.time(),
                        correct=False,
                        anticipation=True,
                        delay=False,
                        click_pos=None,
                        distance_from_center=None
                    )

    def mouseReleaseEvent(self, event):
        if self.state == 'moving':
            click_pos = event.position()
            for obj in self.objects:
                obj_rect = QRectF(obj['pos'].x() - 50, obj['pos'].y() - 50, 100, 100)
                if obj_rect.contains(click_pos):
                    if self.release_time is None:
                        self._emit_result(
                            latency=0,
                            motor_time=0,
                            total_rt=time.time() - self.stimulus_time,
                            correct=False,
                            anticipation=False,
                            delay=False,
                            click_pos=click_pos,
                            distance_from_center=(click_pos - obj['pos']).manhattanLength()
                        )
                    else:
                        self.click_time = time.time()
                        self.click_pos = click_pos
                        correct = obj['is_target']
                        latency = self.release_time - self.stimulus_time
                        motor_time = self.click_time - self.release_time
                        total_rt = self.click_time - self.stimulus_time
                        dist = (click_pos - obj['pos']).manhattanLength()
                        self._emit_result(
                            latency=latency,
                            motor_time=motor_time,
                            total_rt=total_rt,
                            correct=correct,
                            anticipation=False,
                            delay=False,
                            click_pos=click_pos,
                            distance_from_center=dist
                        )
                    return

    def show_stimuli(self):
        if self.state != 'holding':
            return
        self.state = 'stimulus_shown'
        self.stimulus_time = time.time()

        shapes = ['circle', 'square']
        colors = [
            QColor(255, 179, 186),  # red
            QColor(181, 234, 215),  # green
            QColor(255, 224, 179),  # yellow
            QColor(199, 206, 234)   # blue
        ]

        w, h = self.parent.width(), self.parent.height()
        self.objects = []

        margin = 250
        available_width = w - 2 * margin
        available_height = h - 2 * margin

        pos1 = QPointF(
            margin + random.uniform(0, available_width),
            margin + random.uniform(0, available_height)
        )
        angle1 = random.uniform(0, 2 * math.pi)
        speed1 = 700 / 200.0
        vel1 = QPointF(math.cos(angle1) * speed1, math.sin(angle1) * speed1)
        self.objects.append({
            'pos': pos1,
            'vel': vel1,
            'is_target': True,
            'shape': self.sample_shape,
            'color': self.sample_color
        })

        if random.choice([True, False]):
            shape2 = random.choice([s for s in shapes if s != self.sample_shape])
            color2 = self.sample_color
        else:
            shape2 = self.sample_shape
            color2 = random.choice([c for c in colors if c != self.sample_color])
        pos2 = QPointF(
            margin + random.uniform(0, available_width),
            margin + random.uniform(0, available_height)
        )
        angle2 = random.uniform(0, 2 * math.pi)
        speed2 = 700 / 200.0
        vel2 = QPointF(math.cos(angle2) * speed2, math.sin(angle2) * speed2)
        self.objects.append({
            'pos': pos2,
            'vel': vel2,
            'is_target': False,
            'shape': shape2,
            'color': color2
        })

        self.state = 'moving'
        self.timer.start(16)

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(lambda: self._emit_result(
            latency=0, motor_time=0, total_rt=5.0,
            correct=False, anticipation=False, delay=True,
            click_pos=None, distance_from_center=None
        ))
        self.timeout_timer.start(5000)

        self.parent.update()

    def update_positions(self):
        if self.parent is None or not hasattr(self.parent, 'width'):
            self.stop_timers()
            return

        w, h = self.parent.width(), self.parent.height()
        for obj in self.objects:
            obj['pos'] += obj['vel']
            if obj['pos'].x() < 80 or obj['pos'].x() > w - 80:
                obj['vel'].setX(-obj['vel'].x())
            if obj['pos'].y() < 80 or obj['pos'].y() > h - 80:
                obj['vel'].setY(-obj['vel'].y())
        self.parent.update()

    def _emit_result(self, latency, motor_time, total_rt, correct, anticipation, delay, click_pos, distance_from_center):
        self.stop_timers()
        result = {
            'latency': latency,
            'motor_time': motor_time,
            'total_rt': total_rt,
            'correct': correct,
            'anticipation': anticipation,
            'delay': delay,
            'click_x': click_pos.x() if click_pos else None,
            'click_y': click_pos.y() if click_pos else None,
            'distance_from_center': distance_from_center
        }
        self.finished.emit(result)
        self.state = 'finished'
        if hasattr(self.parent, 'update'):
            self.parent.update()

    def stop_timers(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()