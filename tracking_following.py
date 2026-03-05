# tests/tracking_following.py (исправленная версия)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF, pyqtSlot
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QCursor
import time
import random
import math
from config import COLORS

class TrackingFollowingTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.cursor_positions = []
        self.stimulus_positions = []
        self.speed_levels = [80, 120, 160]
        self.current_speed_idx = 0
        self.speed_change_times = [3.0, 6.0]
        self.total_duration = 9.0
        self.stimulus_pos = None
        self.stimulus_vel = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.last_update = None
        self.button_rect = None
        self.trajectory_points = []
        self.max_trajectory_points = 100
        self.distances = []
        self.test_started = False
        
        # Таймер для отслеживания позиции курсора
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.track_cursor)
        self.cursor_timer.setInterval(16)  # ~60 FPS

    def get_button_rect(self):
        if not self.parent:
            return QRectF(0, 0, 160, 60)
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 100, 160, 60)

    def paint(self, painter):
        if not self.parent:
            return
            
        w, h = self.parent.width(), self.parent.height()
        
        # Фон
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        
        # Устанавливаем шрифт
        font = QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(11)
        painter.setFont(font)
        
        painter.setPen(COLORS['text'])

        if self.state != 'finished' and self.state != 'running':
            pressed = self.state == 'holding'
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Тест на слежение - Нажмите СТАРТ")
            
            explanation = "Следите за движущимся кругом курсором мыши"
            painter.drawText(QRectF(0, 50, w, 40), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           explanation)
        
        elif self.state == 'running':
            # Информация
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, w, 80)
            
            painter.setPen(COLORS['text'])
            elapsed = time.time() - self.start_time
            remaining = max(0, self.total_duration - elapsed)
            
            speed = self.speed_levels[self.current_speed_idx]
            painter.drawText(20, 30, f"Время: {elapsed:.1f} с / {self.total_duration:.1f} с")
            painter.drawText(20, 55, f"Скорость: {speed} px/с")
            
            # Среднее расстояние
            if self.distances:
                avg_dist = sum(self.distances) / len(self.distances)
                painter.drawText(w - 250, 30, f"Среднее расстояние: {avg_dist:.1f} px")
            
            # Количество собранных точек
            if self.cursor_positions:
                painter.drawText(w - 250, 55, f"Точек данных: {len(self.cursor_positions)}")
            
            # Отрисовка траектории стимула
            if len(self.trajectory_points) > 1:
                painter.setPen(QPen(COLORS['trajectory'], 1))
                for i in range(1, len(self.trajectory_points)):
                    p1 = self.trajectory_points[i-1]
                    p2 = self.trajectory_points[i]
                    painter.drawLine(int(p1.x()), int(p1.y()), int(p2.x()), int(p2.y()))
            
            # Отрисовка стимула (движущийся круг)
            if self.stimulus_pos:
                # Внешний круг
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(COLORS['stimulus']))
                stimulus_radius = 25
                painter.drawEllipse(QRectF(
                    self.stimulus_pos.x() - stimulus_radius,
                    self.stimulus_pos.y() - stimulus_radius,
                    stimulus_radius * 2, stimulus_radius * 2
                ))
                
                # Внутренний круг
                painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
                inner_radius = 15
                painter.drawEllipse(QRectF(
                    self.stimulus_pos.x() - inner_radius,
                    self.stimulus_pos.y() - inner_radius,
                    inner_radius * 2, inner_radius * 2
                ))
                
                # Центр
                painter.setBrush(QBrush(QColor(0, 0, 0)))
                painter.drawEllipse(QRectF(
                    self.stimulus_pos.x() - 3,
                    self.stimulus_pos.y() - 3,
                    6, 6
                ))
            
            # Получаем текущую позицию курсора
            cursor_pos = self.parent.mapFromGlobal(QCursor.pos())
            
            # Отрисовка курсора (цель слежения)
            # Внешний круг курсора
            painter.setPen(QPen(COLORS['cursor'], 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            cursor_radius = 30
            painter.drawEllipse(QRectF(
                cursor_pos.x() - cursor_radius,
                cursor_pos.y() - cursor_radius,
                cursor_radius * 2, cursor_radius * 2
            ))
            
            # Внутренний круг курсора
            painter.setPen(QPen(COLORS['zone'], 1))
            inner_cursor_radius = 10
            painter.drawEllipse(QRectF(
                cursor_pos.x() - inner_cursor_radius,
                cursor_pos.y() - inner_cursor_radius,
                inner_cursor_radius * 2, inner_cursor_radius * 2
            ))
            
            # Центр курсора
            painter.setBrush(QBrush(COLORS['zone']))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(
                cursor_pos.x() - 5,
                cursor_pos.y() - 5,
                10, 10
            ))
            
            # Линия от курсора до стимула (если далеко)
            if self.stimulus_pos:
                distance = math.hypot(cursor_pos.x() - self.stimulus_pos.x(), 
                                     cursor_pos.y() - self.stimulus_pos.y())
                if distance > 50:
                    painter.setPen(QPen(QColor(255, 100, 100, 150), 1, Qt.PenStyle.DashLine))
                    painter.drawLine(int(cursor_pos.x()), int(cursor_pos.y()), 
                                   int(self.stimulus_pos.x()), int(self.stimulus_pos.y()))

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn']
        if pressed:
            color = color.darker(120)
            
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "СТАРТ")

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.state = 'holding'
                if self.parent:
                    self.parent.update()
                QTimer.singleShot(300, self.start_test)

    @pyqtSlot()
    def track_cursor(self):
        """Отслеживание позиции курсора"""
        if self.state == 'running' and self.test_started and self.stimulus_pos:
            # Получаем текущую позицию курсора
            cursor_pos = self.parent.mapFromGlobal(QCursor.pos())
            
            # Проверяем, находится ли курсор в пределах виджета
            widget_rect = self.parent.rect()
            
            # Преобразуем QPoint в QPointF для сравнения
            cursor_pos_f = QPointF(cursor_pos)
            
            if widget_rect.contains(cursor_pos_f.toPoint()):
                # Сохраняем позицию курсора
                self.cursor_positions.append(QPointF(cursor_pos))
                
                # Сохраняем позицию стимула
                self.stimulus_positions.append(QPointF(self.stimulus_pos))
                
                # Рассчитываем расстояние
                distance = math.hypot(cursor_pos.x() - self.stimulus_pos.x(),
                                     cursor_pos.y() - self.stimulus_pos.y())
                self.distances.append(distance)
                
                # Добавляем точку в траекторию
                self.trajectory_points.append(QPointF(self.stimulus_pos))
                if len(self.trajectory_points) > self.max_trajectory_points:
                    self.trajectory_points.pop(0)

    def start_test(self):
        """Начать тест"""
        print("=" * 50)
        print("НАЧАЛО ТЕСТА НА СЛЕЖЕНИЕ")
        print("Следите за движущимся кругом курсором мыши")
        print("=" * 50)
        
        self.state = 'running'
        self.start_time = time.time()
        self.last_update = time.time()
        
        # Инициализируем позицию стимула
        w, h = self.parent.width(), self.parent.height()
        self.stimulus_pos = QPointF(w/2, h/2)
        
        # Начальная скорость
        angle = random.uniform(0, 2 * math.pi)
        speed_px_per_s = self.speed_levels[0]
        speed_px_per_frame = speed_px_per_s / 60  # 60 FPS
        
        self.stimulus_vel = QPointF(
            math.cos(angle) * speed_px_per_frame,
            math.sin(angle) * speed_px_per_frame
        )
        
        # Очищаем данные
        self.cursor_positions = []
        self.stimulus_positions = []
        self.trajectory_points = []
        self.distances = []
        self.current_speed_idx = 0
        self.test_started = True
        
        # Запускаем таймеры
        self.timer.start(16)  # ~60 FPS для движения стимула
        self.cursor_timer.start(16)  # ~60 FPS для отслеживания курсора
        
        # Устанавливаем фокус на виджет, чтобы получать события мыши
        if self.parent:
            self.parent.setFocus()
            self.parent.update()
        
        print("Тест начался. Двигайте мышью, чтобы следить за кругом.")

    def update_position(self):
        """Обновить позицию стимула"""
        if not self.parent or not hasattr(self.parent, 'width'):
            self.stop_timers()
            return

        now = time.time()
        elapsed = now - self.start_time
        
        # Проверяем завершение теста
        if elapsed >= self.total_duration:
            self.finish_test()
            return
        
        # Проверяем изменение скорости
        if (self.current_speed_idx < len(self.speed_change_times) and 
            elapsed >= self.speed_change_times[self.current_speed_idx]):
            self.current_speed_idx += 1
            print(f"Скорость увеличена до {self.speed_levels[self.current_speed_idx]} px/с")
        
        dt = now - self.last_update
        self.last_update = now
        
        w, h = self.parent.width(), self.parent.height()
        
        # Обновляем скорость
        speed_px_per_s = self.speed_levels[self.current_speed_idx]
        speed_px_per_frame = speed_px_per_s / 60  # 60 FPS
        
        # Добавляем небольшой случайный шум к направлению
        magnitude = math.hypot(self.stimulus_vel.x(), self.stimulus_vel.y())
        if magnitude > 0:
            current_angle = math.atan2(self.stimulus_vel.y(), self.stimulus_vel.x())
            # Небольшой случайный поворот (максимум 15 градусов)
            angle_noise = random.uniform(-0.26, 0.26)  # ±15 градусов
            new_angle = current_angle + angle_noise
            
            # Нормализуем скорость
            self.stimulus_vel = QPointF(
                math.cos(new_angle) * speed_px_per_frame,
                math.sin(new_angle) * speed_px_per_frame
            )
        else:
            # Если скорость нулевая, задаем случайное направление
            angle = random.uniform(0, 2 * math.pi)
            self.stimulus_vel = QPointF(
                math.cos(angle) * speed_px_per_frame,
                math.sin(angle) * speed_px_per_frame
            )
        
        # Обновляем позицию
        new_pos = self.stimulus_pos + self.stimulus_vel
        
        # Проверка границ с отскоком
        margin = 40
        bounced = False
        
        if new_pos.x() < margin:
            self.stimulus_vel.setX(abs(self.stimulus_vel.x()))
            new_pos.setX(margin)
            bounced = True
        elif new_pos.x() > w - margin:
            self.stimulus_vel.setX(-abs(self.stimulus_vel.x()))
            new_pos.setX(w - margin)
            bounced = True
            
        if new_pos.y() < margin:
            self.stimulus_vel.setY(abs(self.stimulus_vel.y()))
            new_pos.setY(margin)
            bounced = True
        elif new_pos.y() > h - margin:
            self.stimulus_vel.setY(-abs(self.stimulus_vel.y()))
            new_pos.setY(h - margin)
            bounced = True
        
        # Если был отскок, немного меняем направление
        if bounced:
            angle = math.atan2(self.stimulus_vel.y(), self.stimulus_vel.x())
            angle += random.uniform(-0.5, 0.5)  # Больший разброс при отскоке
            self.stimulus_vel = QPointF(
                math.cos(angle) * speed_px_per_frame,
                math.sin(angle) * speed_px_per_frame
            )
        
        self.stimulus_pos = new_pos
        
        if self.parent:
            self.parent.update()

    def finish_test(self):
        """Завершить тест"""
        self.stop_timers()
        self.state = 'finished'
        self.test_started = False
        
        print("=" * 50)
        print("ТЕСТ НА СЛЕЖЕНИЕ ЗАВЕРШЕН")
        
        # Отладочная информация
        print(f"Собрано позиций курсора: {len(self.cursor_positions)}")
        print(f"Собрано позиций стимула: {len(self.stimulus_positions)}")
        print(f"Собрано расстояний: {len(self.distances)}")
        
        # Убедимся, что у нас достаточно данных
        if len(self.cursor_positions) == 0 or len(self.stimulus_positions) == 0:
            print("Предупреждение: данных недостаточно, используем последнюю позицию курсора")
            
            # Используем последнюю известную позицию курсора
            cursor_pos = self.parent.mapFromGlobal(QCursor.pos())
            if self.stimulus_pos:
                distance = math.hypot(cursor_pos.x() - self.stimulus_pos.x(),
                                     cursor_pos.y() - self.stimulus_pos.y())
                avg_dist = distance
                max_dist = distance
                hit_rate = 100 if distance <= 50 else 0
            else:
                avg_dist = 0
                max_dist = 0
                hit_rate = 0
            
            result = {
                'test_name': 'Слежение',
                'latency': 0,
                'motor_time': 0,
                'total_rt': self.total_duration,
                'correct': True,
                'anticipation': False,
                'delay': False,
                'click_x': cursor_pos.x(),
                'click_y': cursor_pos.y(),
                'distance_from_center': avg_dist,
                'avg_distance_px': avg_dist,
                'max_distance_px': max_dist,
                'hit_rate_50_percent': hit_rate
            }
            self.finished.emit(result)
            return
        
        # Обрезаем массивы до одинаковой длины
        min_length = min(len(self.cursor_positions), len(self.stimulus_positions))
        
        if min_length == 0:
            print("Ошибка: Не собрано достаточно данных")
            result = {
                'test_name': 'Слежение',
                'latency': 0,
                'motor_time': 0,
                'total_rt': self.total_duration,
                'correct': True,
                'anticipation': False,
                'delay': False,
                'click_x': None,
                'click_y': None,
                'distance_from_center': 0,
                'avg_distance_px': 0,
                'max_distance_px': 0,
                'hit_rate_50_percent': 0
            }
            self.finished.emit(result)
            return
        
        cursor_positions = self.cursor_positions[:min_length]
        stimulus_positions = self.stimulus_positions[:min_length]
        
        # Рассчитываем расстояния
        distances = []
        for i in range(min_length):
            cursor_pos = cursor_positions[i]
            stim_pos = stimulus_positions[i]
            dist = math.hypot(cursor_pos.x() - stim_pos.x(), 
                             cursor_pos.y() - stim_pos.y())
            distances.append(dist)
        
        # Статистика
        if distances:
            avg_dist = sum(distances) / len(distances)
            max_dist = max(distances)
            hit_count = sum(1 for d in distances if d <= 50)
            hit_rate = (hit_count / len(distances) * 100)
        else:
            avg_dist = 0
            max_dist = 0
            hit_rate = 0
        
        print(f"Среднее расстояние: {avg_dist:.1f} px")
        print(f"Максимальное расстояние: {max_dist:.1f} px")
        print(f"Попадания в радиус 50px: {hit_rate:.1f}%")
        print(f"Всего измерений: {len(distances)}")
        print("=" * 50)
        
        # Последняя позиция курсора
        last_cursor = cursor_positions[-1] if cursor_positions else self.parent.mapFromGlobal(QCursor.pos())
        
        result = {
            'test_name': 'Слежение',
            'latency': 0,
            'motor_time': 0,
            'total_rt': self.total_duration,
            'correct': True,
            'anticipation': False,
            'delay': False,
            'click_x': last_cursor.x(),
            'click_y': last_cursor.y(),
            'distance_from_center': avg_dist,
            'avg_distance_px': avg_dist,
            'max_distance_px': max_dist,
            'hit_rate_50_percent': hit_rate
        }
        self.finished.emit(result)

    def stop_timers(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.cursor_timer.isActive():
            self.cursor_timer.stop()