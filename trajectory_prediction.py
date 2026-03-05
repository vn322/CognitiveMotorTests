# tests/trajectory_prediction.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF, QLineF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import time
import random
import math
from config import COLORS

class TrajectoryPredictionTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.object_pos = None
        self.object_vel = None
        self.object_acc = None
        self.prediction_time = 1.5
        self.click_time = None
        self.click_pos = None
        self.predicted_pos = None
        self.trajectory = []
        self.button_rect = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_object)
        self.show_trajectory = True
        self.trajectory_length = 100
        self.prediction_accuracy = 0
        self.real_final_pos = None
        self.timeout_timer = None
        self.observation_start_time = None

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

        if self.state != 'finished':
            pressed = self.state in ('holding', 'moving', 'predicting')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Наблюдайте за движением объекта, затем предскажите его позицию через 1.5 секунды")
        
        elif self.state == 'moving':
            # Отображаем траекторию
            if self.show_trajectory and len(self.trajectory) > 1:
                painter.setPen(QPen(QColor(100, 100, 255, 150), 2))
                for i in range(1, len(self.trajectory)):
                    p1 = self.trajectory[i-1]
                    p2 = self.trajectory[i]
                    painter.drawLine(QLineF(p1, p2))
            
            # Отображаем объект
            if self.object_pos:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 100, 100)))
                painter.drawEllipse(QRectF(
                    self.object_pos.x() - 20,
                    self.object_pos.y() - 20,
                    40, 40
                ))
            
            painter.setPen(COLORS['text'])
            painter.drawText(10, 30, "Наблюдайте за движением...")
            if self.observation_start_time:
                elapsed = time.time() - self.observation_start_time
                painter.drawText(10, 60, f"Время наблюдения: {elapsed:.1f}с")
        
        elif self.state == 'predicting':
            # Отображаем последнюю видимую позицию
            if self.object_pos:
                painter.setPen(QPen(QColor(255, 100, 100, 100), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(255, 100, 100, 50)))
                painter.drawEllipse(QRectF(
                    self.object_pos.x() - 20,
                    self.object_pos.y() - 20,
                    40, 40
                ))
            
            painter.setPen(COLORS['text'])
            painter.drawText(QRectF(0, 0, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Кликните, где будет объект через 1.5 секунды!")
            if self.start_time:
                painter.drawText(10, 30, f"Время на предсказание: {time.time() - self.start_time:.1f}с")

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn'].darker(120) if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Старт")

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.start_time = time.time()
                self.state = 'holding'
                self.button_rect = btn_rect
                self.parent.update()
                QTimer.singleShot(1000, self.start_movement)

    def mouseReleaseEvent(self, event):
        if self.state == 'predicting':
            self.click_time = time.time()
            self.click_pos = event.position()
            self.calculate_prediction_accuracy()
            self._emit_result()

    def start_movement(self):
        if self.state != 'holding':
            return
        
        self.state = 'moving'
        self.observation_start_time = time.time()
        
        if not self.parent:
            return
            
        w, h = self.parent.width(), self.parent.height()
        
        # Начальная позиция
        self.object_pos = QPointF(
            random.uniform(100, w - 100),
            random.uniform(100, h - 200)
        )
        
        # Начальная скорость
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(150, 300) / 1000.0 * 16
        self.object_vel = QPointF(math.cos(angle) * speed, math.sin(angle) * speed)
        
        # Начальное ускорение
        self.object_acc = QPointF(
            random.uniform(-0.5, 0.5),
            random.uniform(-0.5, 0.5)
        )
        
        self.trajectory = [QPointF(self.object_pos)]
        self.timer.start(16)
        
        # Время наблюдения (3-5 секунд)
        observation_time = random.uniform(3.0, 5.0)
        QTimer.singleShot(int(observation_time * 1000), self.start_prediction)

    def update_object(self):
        if not self.parent:
            self.timer.stop()
            return
        
        w, h = self.parent.width(), self.parent.height()
        
        # Обновляем ускорение
        if random.random() < 0.1:
            self.object_acc = QPointF(
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5)
            )
        
        # Обновляем скорость
        self.object_vel += self.object_acc
        
        # Ограничиваем скорость
        speed = math.hypot(self.object_vel.x(), self.object_vel.y())
        max_speed = 500 / 1000.0 * 16
        if speed > max_speed:
            scale = max_speed / speed
            self.object_vel *= scale
        
        # Обновляем позицию
        self.object_pos += self.object_vel
        
        # Отражение от границ
        if self.object_pos.x() < 20:
            self.object_pos.setX(20)
            self.object_vel.setX(-self.object_vel.x() * 0.8)
        elif self.object_pos.x() > w - 20:
            self.object_pos.setX(w - 20)
            self.object_vel.setX(-self.object_vel.x() * 0.8)
        
        if self.object_pos.y() < 20:
            self.object_pos.setY(20)
            self.object_vel.setY(-self.object_vel.y() * 0.8)
        elif self.object_pos.y() > h - 120:
            self.object_pos.setY(h - 120)
            self.object_vel.setY(-self.object_vel.y() * 0.8)
        
        # Сохраняем траекторию
        self.trajectory.append(QPointF(self.object_pos))
        if len(self.trajectory) > self.trajectory_length:
            self.trajectory.pop(0)
        
        self.parent.update()

    def start_prediction(self):
        if self.state != 'moving':
            return
        
        self.state = 'predicting'
        self.timer.stop()
        
        if not self.parent:
            return
            
        # Сохраняем последние параметры
        last_pos = self.object_pos
        last_vel = self.object_vel
        last_acc = self.object_acc
        
        # Вычисляем предсказанную позицию
        t = self.prediction_time
        predicted_x = last_pos.x() + last_vel.x() * t + 0.5 * last_acc.x() * t * t
        predicted_y = last_pos.y() + last_vel.y() * t + 0.5 * last_acc.y() * t * t
        
        w, h = self.parent.width(), self.parent.height()
        predicted_x = max(20, min(w - 20, predicted_x))
        predicted_y = max(20, min(h - 120, predicted_y))
        
        self.predicted_pos = QPointF(predicted_x, predicted_y)
        
        # Симулируем реальное движение
        self.simulate_real_movement(last_pos, last_vel, last_acc)
        
        # Таймаут на предсказание
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(lambda: self._emit_result_timeout())
        self.timeout_timer.start(3000)
        
        self.parent.update()

    def simulate_real_movement(self, start_pos, start_vel, start_acc):
        if not self.parent:
            return
            
        self.real_trajectory = []
        pos = QPointF(start_pos)
        vel = QPointF(start_vel)
        acc = QPointF(start_acc)
        
        dt = 0.016
        steps = int(self.prediction_time / dt)
        w, h = self.parent.width(), self.parent.height()
        
        for _ in range(steps):
            if random.random() < 0.05:
                acc = QPointF(
                    random.uniform(-0.3, 0.3),
                    random.uniform(-0.3, 0.3)
                )
            
            vel += acc * dt
            
            speed = math.hypot(vel.x(), vel.y())
            max_speed = 500 / 1000.0 * 16
            if speed > max_speed:
                scale = max_speed / speed
                vel *= scale
            
            pos += vel * dt
            
            if pos.x() < 20:
                pos.setX(20)
                vel.setX(-vel.x() * 0.8)
            elif pos.x() > w - 20:
                pos.setX(w - 20)
                vel.setX(-vel.x() * 0.8)
            
            if pos.y() < 20:
                pos.setY(20)
                vel.setY(-vel.y() * 0.8)
            elif pos.y() > h - 120:
                pos.setY(h - 120)
                vel.setY(-vel.y() * 0.8)
            
            self.real_trajectory.append(QPointF(pos))
        
        self.real_final_pos = pos

    def calculate_prediction_accuracy(self):
        if not self.click_pos or not self.real_final_pos or not self.parent:
            self.prediction_accuracy = 0
            return
        
        distance = math.hypot(
            self.click_pos.x() - self.real_final_pos.x(),
            self.click_pos.y() - self.real_final_pos.y()
        )
        
        max_distance = math.hypot(self.parent.width(), self.parent.height())
        self.prediction_accuracy = max(0, 100 - (distance / max_distance * 100))

    def _emit_result(self):
        if self.timeout_timer:
            self.timeout_timer.stop()
        
        distance = 0
        model_error = 0
        
        if self.click_pos and self.real_final_pos:
            distance = math.hypot(
                self.click_pos.x() - self.real_final_pos.x(),
                self.click_pos.y() - self.real_final_pos.y()
            )
            
        if self.predicted_pos and self.real_final_pos:
            model_error = math.hypot(
                self.predicted_pos.x() - self.real_final_pos.x(),
                self.predicted_pos.y() - self.real_final_pos.y()
            )
        
        observation_time = 0
        if self.observation_start_time and self.start_time:
            observation_time = self.start_time - self.observation_start_time
        
        result = {
            'latency': 0,
            'motor_time': self.click_time - self.start_time if self.click_time else 0,
            'total_rt': self.click_time - self.observation_start_time if self.click_time and self.observation_start_time else 0,
            'correct': self.prediction_accuracy > 70,
            'anticipation': False,
            'delay': False,
            'click_x': self.click_pos.x() if self.click_pos else None,
            'click_y': self.click_pos.y() if self.click_pos else None,
            'distance_from_center': None,
            'test_name': 'Предвидение траектории',
            'prediction_accuracy': self.prediction_accuracy,
            'prediction_time': self.prediction_time,
            'observation_time': observation_time,
            'prediction_error_px': distance,
            'model_error_px': model_error
        }
        self.finished.emit(result)
        self.state = 'finished'
        if self.parent:
            self.parent.update()

    def _emit_result_timeout(self):
        observation_time = 0
        if self.observation_start_time and self.start_time:
            observation_time = self.start_time - self.observation_start_time
            
        result = {
            'latency': 0,
            'motor_time': 0,
            'total_rt': 3.0,
            'correct': False,
            'anticipation': False,
            'delay': True,
            'click_x': None,
            'click_y': None,
            'distance_from_center': None,
            'test_name': 'Предвидение траектории',
            'prediction_accuracy': 0,
            'prediction_time': self.prediction_time,
            'observation_time': observation_time,
            'prediction_error_px': 0,
            'model_error_px': 0
        }
        self.finished.emit(result)
        self.state = 'finished'
        if self.parent:
            self.parent.update()

    def stop_timers(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()