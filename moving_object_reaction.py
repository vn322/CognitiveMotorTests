# tests/moving_object_reaction.py (исправленная версия)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import time
import random
import math
from config import COLORS

class MovingObjectReactionTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.click_time = None
        self.stimulus_pos = None
        self.stimulus_vel = None
        self.center_zone_radius = 50
        self.click_pos = None
        self.cross_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timeout_timer = None
        self.trajectory_type = None
        self.trajectory_angle = 0
        self.button_rect = None
        self.has_clicked = False
        self.stimulus_in_zone = False
        self.center_x = 0
        self.center_y = 0
        self.total_distance = 0
        self.speed = 0
        self.stimulus_radius = 15

    def get_button_rect(self):
        if not self.parent:
            return QRectF(0, 0, 160, 60)
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 100, 160, 60)

    def paint(self, painter):
        if not self.parent:
            return
            
        w, h = self.parent.width(), self.parent.height()
        self.center_x, self.center_y = w / 2, h / 2
        
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        painter.setPen(COLORS['text'])
        
        # Устанавливаем шрифт
        font = QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(11)
        painter.setFont(font)

        if self.state != 'finished':
            pressed = self.state in ('holding', 'moving')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Нажмите СТАРТ. Кликните, когда стимул будет в центральной зоне.")
            
            # Предварительно показываем зону
            self.draw_zone(painter)
        
        elif self.state == 'moving':
            # Отрисовка фона информации
            painter.setBrush(QBrush(COLORS['info_bg']))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, w, 120)
            
            # Сначала зона
            self.draw_zone(painter)
            
            # Траектория (линия, по которой движется стимул)
            if self.stimulus_pos and self.stimulus_vel:
                painter.setPen(QPen(COLORS['trajectory_line'], 2, Qt.PenStyle.DashLine))
                # Рисуем всю траекторию от края до края экрана
                line_length = max(w, h) * 0.8
                
                # Начальная точка на границе экрана
                start_x = self.center_x - math.cos(self.trajectory_angle) * line_length
                start_y = self.center_y - math.sin(self.trajectory_angle) * line_length
                
                # Конечная точка на противоположной границе
                end_x = self.center_x + math.cos(self.trajectory_angle) * line_length
                end_y = self.center_y + math.sin(self.trajectory_angle) * line_length
                
                painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))
            
            # Стимул
            if self.stimulus_pos:
                # Проверяем, виден ли стимул на экране
                visible_buffer = 50
                if (self.stimulus_pos.x() >= -visible_buffer and 
                    self.stimulus_pos.x() <= w + visible_buffer and
                    self.stimulus_pos.y() >= -visible_buffer and 
                    self.stimulus_pos.y() <= h + visible_buffer):
                    
                    # Основной круг стимула
                    painter.setPen(Qt.PenStyle.NoPen)
                    if self.stimulus_in_zone:
                        painter.setBrush(QBrush(COLORS['stimulus_in_zone']))
                    else:
                        painter.setBrush(QBrush(COLORS['stimulus']))
                    
                    painter.drawEllipse(QRectF(
                        self.stimulus_pos.x() - self.stimulus_radius,
                        self.stimulus_pos.y() - self.stimulus_radius,
                        self.stimulus_radius * 2, self.stimulus_radius * 2
                    ))
                    
                    # Центр стимула (черная точка)
                    painter.setBrush(QBrush(QColor(0, 0, 0)))
                    painter.drawEllipse(QRectF(
                        self.stimulus_pos.x() - 3,
                        self.stimulus_pos.y() - 3,
                        6, 6
                    ))
            
            # Информация
            painter.setPen(COLORS['text'])
            
            # Название траектории
            if self.trajectory_type:
                trajectory_names = {
                    'horizontal_left': "→ Горизонтально: слева направо",
                    'horizontal_right': "← Горизонтально: справа налево", 
                    'vertical_down': "↓ Вертикально: сверху вниз",
                    'vertical_up': "↑ Вертикально: снизу вверх",
                    'diagonal_down': "↘ Диагонально: сверху слева вниз направо",
                    'diagonal_up': "↗ Диагонально: снизу справа вверх налево",
                    'diagonal_down_rev': "↙ Диагонально: сверху справа вниз налево",
                    'diagonal_up_rev': "↖ Диагонально: снизу слева вверх направо"
                }
                
                painter.drawText(20, 30, f"Траектория: {trajectory_names.get(self.trajectory_type, '')}")
            
            # Время
            if self.start_time:
                elapsed = time.time() - self.start_time
                painter.drawText(20, 55, f"Время: {elapsed:.2f} с")
                
                # Расстояние до центра
                if self.stimulus_pos:
                    distance_to_center = math.hypot(
                        self.stimulus_pos.x() - self.center_x,
                        self.stimulus_pos.y() - self.center_y
                    )
                    painter.drawText(20, 80, f"Расстояние до центра: {distance_to_center:.0f} px")
                
                # Сообщение о зоне
                if self.stimulus_in_zone and not self.has_clicked:
                    painter.setPen(QColor(0, 150, 0))
                    painter.drawText(QRectF(0, 100, w, 40), 
                                   Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                                   "СТИМУЛ В ЗОНЕ! КЛИКАЙТЕ!")
                elif self.cross_time and not self.has_clicked:
                    time_to_center = max(0, self.cross_time - time.time())
                    if time_to_center < 5:  # Показываем только последние 5 секунд
                        painter.drawText(20, 105, f"Стимул в центре через: {time_to_center:.1f} с")

    def draw_zone(self, painter):
        """Отрисовка центральной зоны"""
        center = QPointF(self.center_x, self.center_y)
        
        # Внешняя зона (полупрозрачная)
        painter.setPen(QPen(COLORS['zone_outer'], 3))
        painter.setBrush(QBrush(COLORS['zone_outer']))
        painter.drawEllipse(center, self.center_zone_radius, self.center_zone_radius)
        
        # Внутренний круг
        painter.setPen(QPen(COLORS['zone_inner'], 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inner_radius = 15
        painter.drawEllipse(center, inner_radius, inner_radius)
        
        # Крест в центре
        painter.setPen(QPen(COLORS['zone_inner'], 2))
        cross_size = 20
        painter.drawLine(int(self.center_x - cross_size), int(self.center_y), 
                        int(self.center_x + cross_size), int(self.center_y))
        painter.drawLine(int(self.center_x), int(self.center_y - cross_size), 
                        int(self.center_x), int(self.center_y + cross_size))

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn_pressed'] if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "СТАРТ")

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.start_time = time.time()
                self.state = 'holding'
                self.button_rect = btn_rect
                if self.parent:
                    self.parent.update()
                delay = random.uniform(0.5, 1.0)  # Случайная задержка 0.5-1.0 сек
                QTimer.singleShot(int(delay * 1000), self.start_movement)

    def mouseReleaseEvent(self, event):
        if self.state == 'moving' and not self.has_clicked:
            self.has_clicked = True
            self.click_time = time.time()
            self.click_pos = event.position()
            self.stop_timers()
            
            # Вычисляем время реакции
            if self.cross_time:
                timing_error = self.click_time - self.cross_time
            else:
                timing_error = 0
            
            # Расстояние от клика до стимула
            distance_to_stimulus = 0
            if self.stimulus_pos and self.click_pos:
                distance_to_stimulus = math.hypot(
                    self.click_pos.x() - self.stimulus_pos.x(),
                    self.click_pos.y() - self.stimulus_pos.y()
                )
            
            # Определяем, был ли клик в зоне
            click_in_zone = False
            if self.click_pos:
                distance_to_center = math.hypot(
                    self.click_pos.x() - self.center_x,
                    self.click_pos.y() - self.center_y
                )
                click_in_zone = distance_to_center <= self.center_zone_radius
            
            # Считаем реакцию правильной, если:
            # 1. Клик сделан, когда стимул был в зоне
            # 2. Временная ошибка не слишком велика (±0.25 сек)
            correct = False
            if self.stimulus_in_zone and abs(timing_error) < 0.25:
                if click_in_zone or distance_to_stimulus < (self.center_zone_radius + self.stimulus_radius):
                    correct = True
            
            self._emit_result(
                latency=0,
                motor_time=0,
                total_rt=self.click_time - self.start_time if self.click_time else 0,
                correct=correct,
                anticipation=timing_error < -0.05,  # Преждевременная (>50ms раньше)
                delay=timing_error > 0.05,  # Запаздывающая (>50ms позже)
                click_x=self.click_pos.x() if self.click_pos else None,
                click_y=self.click_pos.y() if self.click_pos else None,
                distance_from_center=distance_to_stimulus,
                timing_delay=timing_error,
                trajectory_type=self.trajectory_type,
                speed=self.speed
            )

    def start_movement(self):
        if self.state != 'holding':
            return
        
        print("=" * 50)
        print("НАЧАЛО НОВОЙ ПОПЫТКИ")
        
        self.state = 'moving'
        self.has_clicked = False
        self.stimulus_in_zone = False
        
        if not self.parent:
            return
            
        w, h = self.parent.width(), self.parent.height()
        self.center_x, self.center_y = w / 2, h / 2
        
        print(f"Размер экрана: {w}x{h}")
        print(f"Центр: ({self.center_x:.0f}, {self.center_y:.0f})")
        
        # Выбираем случайную траекторию (все траектории будут проходить через центр!)
        trajectories = [
            ('horizontal_left', 0),  # Слева направо (→)
            ('horizontal_right', math.pi),  # Справа налево (←)
            ('vertical_down', math.pi/2),  # Сверху вниз (↓)
            ('vertical_up', 3*math.pi/2),  # Снизу вверх (↑)
            ('diagonal_down', math.pi/4),  # Сверху слева вниз направо (↘)
            ('diagonal_up', 5*math.pi/4),  # Снизу справа вверх налево (↗)
            ('diagonal_down_rev', 3*math.pi/4),  # Сверху справа вниз налево (↙)
            ('diagonal_up_rev', 7*math.pi/4),  # Снизу слева вверх направо (↖)
        ]
        
        self.trajectory_type, self.trajectory_angle = random.choice(trajectories)
        print(f"Траектория: {self.trajectory_type}, угол: {self.trajectory_angle:.2f} рад")
        
        # Скорость стимула (150-250 px/s) - оптимальная для реакции
        self.speed = random.uniform(250, 450)
        speed_px_per_frame = self.speed / 60  # 60 FPS
        
        # Вычисляем расстояние от центра до границы экрана по данной траектории
        # Это нужно, чтобы стимул начал движение за пределами экрана
        max_distance = max(w, h) * 0.7
        
        # Начальная позиция - ЗА ГРАНИЦЕЙ ЭКРАНА по направлению траектории
        start_x = self.center_x - math.cos(self.trajectory_angle) * max_distance
        start_y = self.center_y - math.sin(self.trajectory_angle) * max_distance
        
        # Общая длина пути (проходит через центр и выходит с другой стороны)
        self.total_distance = max_distance * 2
        
        # Время, через которое стимул будет в центре
        distance_to_center = math.hypot(start_x - self.center_x, start_y - self.center_y)
        time_to_center = distance_to_center / self.speed
        self.cross_time = time.time() + time_to_center
        
        self.stimulus_pos = QPointF(start_x, start_y)
        self.stimulus_vel = QPointF(
            math.cos(self.trajectory_angle) * speed_px_per_frame,
            math.sin(self.trajectory_angle) * speed_px_per_frame
        )
        
        print(f"Начальная позиция: ({start_x:.0f}, {start_y:.0f})")
        print(f"Скорость: {self.speed:.0f} px/s")
        print(f"Расстояние до центра: {distance_to_center:.0f} px")
        print(f"Время до центра: {time_to_center:.2f} с")
        print(f"Стимул появится через: {max(0, -start_x/abs(self.stimulus_vel.x()) if self.stimulus_vel.x()!=0 else -start_y/abs(self.stimulus_vel.y())):.2f} с")
        
        # Запускаем таймер
        self.timer.start(16)  # ~60 FPS
        
        # Таймаут
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(lambda: self._emit_result_timeout())
        self.timeout_timer.start(12000)  # 12 секунд
        
        if self.parent:
            self.parent.update()

    def update_position(self):
        if not self.parent or not self.stimulus_pos or not self.stimulus_vel:
            if self.timer.isActive():
                self.timer.stop()
            return
            
        w, h = self.parent.width(), self.parent.height()
        
        # Обновляем позицию стимула
        self.stimulus_pos += self.stimulus_vel
        
        # Проверяем, находится ли стимул в центральной зоне
        distance_to_center = math.hypot(
            self.stimulus_pos.x() - self.center_x,
            self.stimulus_pos.y() - self.center_y
        )
        
        # Стимул в зоне, если расстояние меньше суммы радиусов
        self.stimulus_in_zone = distance_to_center <= (self.center_zone_radius + self.stimulus_radius)
        
        # Если стимул вышел далеко за пределы экрана - завершаем тест
        buffer = 100
        if (self.stimulus_pos.x() < -buffer and self.stimulus_vel.x() < 0 or 
            self.stimulus_pos.x() > w + buffer and self.stimulus_vel.x() > 0 or 
            self.stimulus_pos.y() < -buffer and self.stimulus_vel.y() < 0 or 
            self.stimulus_pos.y() > h + buffer and self.stimulus_vel.y() > 0):
            
            if not self.has_clicked:
                print(f"Стимул вышел за пределы экрана.")
                self._emit_result_timeout()
            return
        
        if self.parent:
            self.parent.update()

    def _emit_result_timeout(self):
        self.stop_timers()
        
        print("ТАЙМАУТ - пользователь не успел кликнуть")
        
        result = {
            'latency': 0,
            'motor_time': 0,
            'total_rt': 12.0,  # Время таймаута
            'correct': False,
            'anticipation': False,
            'delay': True,
            'click_x': None,
            'click_y': None,
            'distance_from_center': None,
            'timing_delay': 12.0,
            'trajectory_type': self.trajectory_type,
            'speed': self.speed
        }
        self.finished.emit(result)
        self.state = 'finished'
        if self.parent:
            self.parent.update()

    def _emit_result(self, **kwargs):
        self.stop_timers()
        
        print("=" * 50)
        print("РЕЗУЛЬТАТ ТЕСТА:")
        print(f"  Правильно: {'ДА' if kwargs.get('correct', False) else 'НЕТ'}")
        print(f"  Время реакции: {kwargs.get('total_rt', 0):.3f} с")
        print(f"  Временная ошибка: {kwargs.get('timing_delay', 0):+.3f} с")
        print(f"  Расстояние до стимула: {kwargs.get('distance_from_center', 0):.1f} px")
        print("=" * 50)
        
        self.finished.emit(kwargs)
        self.state = 'finished'
        if self.parent:
            self.parent.update()

    def stop_timers(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()