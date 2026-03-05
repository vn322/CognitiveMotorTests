# tests/combined_b.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
import time
import random
import math
from config import COLORS

class CombinedTestB(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.stimulus_time = None
        self.role_switch_time_abs = None
        self.release_time = None
        self.click_time = None
        self.objects = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_positions)
        self.timeout_timer = None
        self.sample_shape = None
        self.sample_color = None
        self.button_rect = None
        self.roles_switched = False

    def get_button_rect(self):
        if not self.parent:
            return QRectF(0, 0, 160, 60)
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 100, 160, 60)

    def paint(self, painter):
        if not self.parent:
            return
            
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        painter.setPen(COLORS['text'])
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)

        w = self.parent.width()
        h = self.parent.height()

        if self.state == 'waiting_start' and self.sample_shape is None:
            self.sample_shape = random.choice(['circle', 'square'])
            self.sample_color = random.choice([
                QColor(255, 179, 186),  # red
                QColor(181, 234, 215),  # green
                QColor(255, 224, 179),  # yellow
                QColor(199, 206, 234)   # blue
            ])

        if self.sample_shape is not None and self.sample_color is not None:
            self.draw_sample(painter)

        if self.state != 'finished':
            pressed = self.state in ('holding', 'stimulus_shown', 'moving')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                             "Запомните образец. После появления стимулов — кликайте!")
        elif self.state in ('stimulus_shown', 'moving'):
            self.draw_objects(painter)
            if not self.roles_switched:
                painter.drawText(QRectF(0, h - 80, w, 40), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                                 "Кликните на стимул (совпадает с образцом)!")
            else:
                painter.drawText(QRectF(0, h - 80, w, 40), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                                 "Роли сменились! Кликните на НОВЫЙ стимул!")

    def draw_sample(self, painter):
        sample_x, sample_y = 20, 20
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
                self.start_time = time.time()
                self.state = 'holding'
                self.button_rect = btn_rect
                self.safe_update()
                delay = random.uniform(0.5, 2.0)
                QTimer.singleShot(int(delay * 1000), self.show_stimuli)

    def mouseMoveEvent(self, event):
        if self.button_rect and self.state in ('holding', 'stimulus_shown', 'moving'):
            if not self.button_rect.contains(event.position()) and self.release_time is None:
                self.release_time = time.time()
                if self.state == 'holding':
                    self._emit_result(
                        latency=0,
                        motor_time=0,
                        total_rt=self.release_time - self.start_time,
                        correct=False,
                        anticipation=True,
                        delay=False,
                        click_pos=None,
                        distance_from_center=None
                    )

    def mouseReleaseEvent(self, event):
        if self.state == 'moving':  # ← разрешено сразу после появления стимулов
            click_pos = event.position()
            for obj in self.objects:
                obj_rect = QRectF(obj['pos'].x() - 50, obj['pos'].y() - 50, 100, 100)
                if obj_rect.contains(click_pos):
                    self.click_time = time.time()
                    
                    # Определяем, кто сейчас стимул
                    if not self.roles_switched:
                        # До смены: стимул = совпадает с образцом
                        correct = (
                            obj['shape'] == self.sample_shape and
                            obj['color'] == self.sample_color
                        )
                    else:
                        # После смены: стимул = тот, что СТАЛ совпадать с образцом
                        correct = (
                            obj['shape'] == self.sample_shape and
                            obj['color'] == self.sample_color
                        )
                    
                    # Времена
                    if self.roles_switched:
                        latency = self.release_time - self.role_switch_time_abs if self.release_time else 0
                        motor_time = self.click_time - self.release_time if self.release_time else (self.click_time - self.role_switch_time_abs)
                        total_rt = self.click_time - self.role_switch_time_abs
                    else:
                        latency = self.release_time - self.stimulus_time if self.release_time else 0
                        motor_time = self.click_time - self.release_time if self.release_time else (self.click_time - self.stimulus_time)
                        total_rt = self.click_time - self.stimulus_time

                    dist = (click_pos - obj['pos']).manhattanLength()
                    self._emit_result(
                        latency=max(0.0, latency),
                        motor_time=max(0.0, motor_time),
                        total_rt=max(0.0, total_rt),
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
        margin = 250
        available_width = w - 2 * margin
        available_height = h - 2 * margin

        pos_a = QPointF(
            margin + random.uniform(0, available_width),
            margin + random.uniform(0, available_height)
        )
        angle_a = random.uniform(0, 2 * math.pi)
        speed_a = 700 / 200.0
        vel_a = QPointF(math.cos(angle_a) * speed_a, math.sin(angle_a) * speed_a)
        self.obj_a = {
            'pos': pos_a,
            'vel': vel_a,
            'shape': self.sample_shape,
            'color': self.sample_color
        }

        other_colors = [c for c in colors if c != self.sample_color]
        other_shapes = [s for s in shapes if s != self.sample_shape]
        if random.choice([True, False]):
            shape_b = self.sample_shape
            color_b = random.choice(other_colors)
        else:
            shape_b = random.choice(other_shapes)
            color_b = self.sample_color

        pos_b = QPointF(
            margin + random.uniform(0, available_width),
            margin + random.uniform(0, available_height)
        )
        angle_b = random.uniform(0, 2 * math.pi)
        speed_b = 700 / 200.0
        vel_b = QPointF(math.cos(angle_b) * speed_b, math.sin(angle_b) * speed_b)
        self.obj_b = {
            'pos': pos_b,
            'vel': vel_b,
            'shape': shape_b,
            'color': color_b
        }

        self.objects = [self.obj_a, self.obj_b]

        self.state = 'moving'
        self.timer.start(16)

        switch_delay = random.uniform(800, 1500)
        self.role_switch_time_abs = time.time() + switch_delay / 1000.0
        QTimer.singleShot(int(switch_delay), self.switch_roles)

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(lambda: self._emit_result(
            latency=0, motor_time=0, total_rt=5.0,
            correct=False, anticipation=False, delay=True,
            click_pos=None, distance_from_center=None
        ))
        self.timeout_timer.start(5000)

        self.safe_update()

    def switch_roles(self):
        if self.state != 'moving':
            return

        try:
            # Проверяем, существует ли еще родительский объект
            if not self.parent:
                return

            # Меняем внешний вид объектов
            pos_a, vel_a = self.obj_a['pos'], self.obj_a['vel']
            pos_b, vel_b = self.obj_b['pos'], self.obj_b['vel']

            # A → становится дистрактором
            self.obj_a['shape'] = self.obj_b['shape']
            self.obj_a['color'] = self.obj_b['color']

            # B → становится стимулом (копия образца)
            self.obj_b['shape'] = self.sample_shape
            self.obj_b['color'] = self.sample_color

            self.obj_a['pos'], self.obj_a['vel'] = pos_a, vel_a
            self.obj_b['pos'], self.obj_b['vel'] = pos_b, vel_b

            self.roles_switched = True
            self.safe_update()
        except RuntimeError:
            # Если объект PyQt был удален, просто выходим
            pass

    def update_positions(self):
        # Проверяем существование родительского объекта
        if not self.parent or not hasattr(self.parent, 'width'):
            self.stop_timers()
            return

        try:
            w, h = self.parent.width(), self.parent.height()
            for obj in self.objects:
                obj['pos'] += obj['vel']
                if obj['pos'].x() < 80 or obj['pos'].x() > w - 80:
                    obj['vel'].setX(-obj['vel'].x())
                if obj['pos'].y() < 80 or obj['pos'].y() > h - 80:
                    obj['vel'].setY(-obj['vel'].y())
            self.safe_update()
        except RuntimeError:
            # Если объект PyQt был удален, останавливаем таймеры
            self.stop_timers()

    def safe_update(self):
        """Безопасный вызов update() с проверкой существования объекта"""
        try:
            if self.parent and hasattr(self.parent, 'update'):
                self.parent.update()
        except RuntimeError:
            # Объект был удален, ничего не делаем
            pass

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
        self.safe_update()

    def stop_timers(self):
        """Остановка всех активных таймеров"""
        try:
            if self.timer.isActive():
                self.timer.stop()
            if self.timeout_timer and self.timeout_timer.isActive():
                self.timeout_timer.stop()
        except RuntimeError:
            # Если таймеры уже были удалены, игнорируем ошибку
            pass