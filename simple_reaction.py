# tests/simple_reaction.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QBrush, QPen
import time
import random
from config import COLORS

class SimpleReactionTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.stimulus_time = None
        self.release_time = None  # Время покидания курсором области кнопки "Старт"
        self.click_time = None    # Время клика на стимуле
        self.stimulus_pos = None
        self.click_pos = None
        self.button_rect = None
        self.timeout_timer = None
        self.stimulus_timer = None
        self.has_left_button_area = False  # Флаг покидания области кнопки "Старт"
        self.error_type = None
        self.error_reason = None
        self.start_button_clicked = False  # Флаг: была ли нажата кнопка "Старт"

    def get_button_rect(self):
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 100, 160, 60)

    def paint(self, painter):
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)
        painter.setPen(COLORS['text'])

        w = self.parent.width()
        h = self.parent.height()

        if self.state in ('waiting_start', 'holding'):
            self.draw_sample(painter)

        if self.state != 'finished':
            pressed = self.state in ('holding', 'stimulus_shown')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                             "Нажмите и удерживайте кнопку «Старт»")
        elif self.state == 'stimulus_shown':
            painter.setBrush(QBrush(COLORS['stimulus']))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(self.stimulus_pos.x() - 50, self.stimulus_pos.y() - 50, 100, 100))

    def draw_sample(self, painter):
        sample_x, sample_y = 20, 20
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(COLORS['stimulus']))
        size = 50
        rect = QRectF(sample_x, sample_y, size, size)
        painter.drawEllipse(rect)

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn_pressed'] if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Старт")

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
            
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.start_time = time.time()
                self.state = 'holding'
                self.button_rect = btn_rect
                self.has_left_button_area = False
                self.release_time = None
                self.start_button_clicked = True
                self.error_type = None
                self.error_reason = None
                self.parent.update()
                delay = random.uniform(0.5, 2.0)
                self.stimulus_timer = QTimer.singleShot(int(delay * 1000), self.show_stimulus)
        
        elif self.state == 'stimulus_shown':
            # Это клик на стимуле
            self.click_time = time.time()
            self.click_pos = event.position()
            
            # Определяем, кликнули ли на стимуле
            on_stimulus = False
            dist = None
            
            if self.stimulus_pos:
                # Область клика на стимуле
                stim_rect = QRectF(self.stimulus_pos.x() - 75, self.stimulus_pos.y() - 75, 150, 150)
                on_stimulus = stim_rect.contains(event.position())
                
                if on_stimulus:
                    # Расстояние от клика до центра стимула
                    dx = event.position().x() - self.stimulus_pos.x()
                    dy = event.position().y() - self.stimulus_pos.y()
                    dist = (dx * dx + dy * dy) ** 0.5  # Евклидово расстояние
            
            # Инициализируем переменные
            latency = 0
            motor_time = 0
            total_rt = 0
            correct = False
            
            if self.stimulus_time:
                total_rt = max(0, self.click_time - self.stimulus_time)
                
                if self.has_left_button_area and self.release_time:
                    # Пользователь покинул область кнопки
                    latency = max(0, self.release_time - self.stimulus_time)
                    
                    if self.release_time and self.click_time:
                        motor_time = max(0, self.click_time - self.release_time)
                    
                    if on_stimulus and dist is not None and dist < 100:  # Допустимая погрешность
                        # Успешная попытка
                        correct = True
                        self.error_type = 'none'
                        self.error_reason = 'Успешная попытка'
                        
                        # ДЕБАГ: Выводим временные метки
                        print(f"DEBUG успешная попытка:")
                        print(f"  Показан стимул: {self.stimulus_time:.3f}")
                        print(f"  Покинул область кнопки: {self.release_time:.3f}")
                        print(f"  Кликнул: {self.click_time:.3f}")
                        print(f"  Латентность: {latency:.3f} сек ({latency*1000:.0f} мс)")
                        print(f"  Моторное время: {motor_time:.3f} сек ({motor_time*1000:.0f} мс)")
                        print(f"  Общее время: {total_rt:.3f} сек ({total_rt*1000:.0f} мс)")
                        print(f"  Расстояние: {dist:.1f}px")
                        print(f"  Покинул область: {self.has_left_button_area}")
                    else:
                        # Промах
                        correct = False
                        if dist is not None:
                            self.error_type = 'miss'
                            self.error_reason = f'Промах (расстояние: {dist:.1f}px)'
                        else:
                            self.error_type = 'miss'
                            self.error_reason = 'Промах (клин мимо стимула)'
                else:
                    # Не покинул область кнопки перед кликом
                    correct = False
                    if on_stimulus:
                        self.error_type = 'no_release'
                        self.error_reason = 'Кликнул на стимуле, не покинув область кнопки'
                    else:
                        if dist is not None:
                            self.error_type = 'no_release_miss'
                            self.error_reason = f'Не покинул область кнопки и промахнулся (расстояние: {dist:.1f}px)'
                        else:
                            self.error_type = 'no_release_miss'
                            self.error_reason = 'Не покинул область кнопки и кликнул мимо стимула'
                    
                    # Даже при ошибке рассчитываем время
                    latency = 0
                    motor_time = total_rt
                
                self._emit_result(
                    latency=latency,
                    motor_time=motor_time,
                    total_rt=total_rt,
                    correct=correct,
                    anticipation=False,
                    delay=False,
                    click_pos=event.position(),
                    distance_from_center=dist
                )

    def mouseMoveEvent(self, event):
        # Отслеживаем движение мыши всегда
        if self.state in ('holding', 'stimulus_shown') and self.button_rect:
            current_pos = event.position()
            
            # Если еще не покинули область кнопки и курсор вне кнопки
            if not self.has_left_button_area and not self.button_rect.contains(current_pos):
                self.has_left_button_area = True
                self.release_time = time.time()
                
                # Если покинули область кнопки до показа стимула - это антиципация
                if self.state == 'holding':
                    self.error_type = 'anticipation'
                    self.error_reason = 'Покинул область кнопки до появления стимула'
                    
                    # Завершаем попытку
                    latency = 0
                    total_rt = self.release_time - self.start_time if self.start_time else 0
                    
                    self._emit_result(
                        latency=latency,
                        motor_time=0,
                        total_rt=total_rt,
                        correct=False,
                        anticipation=True,
                        delay=False,
                        click_pos=None,
                        distance_from_center=None
                    )

    def mouseReleaseEvent(self, event):
        # Не используем mouseReleaseEvent для логики теста
        # Только mousePressEvent для кликов
        pass

    def show_stimulus(self):
        try:
            if not self.parent or not hasattr(self.parent, 'width'):
                return
                
            if self.state != 'holding':
                return
                
            self.state = 'stimulus_shown'
            self.stimulus_time = time.time()
            
            w, h = self.parent.width(), self.parent.height()
            
            margin_x = w // 4
            margin_y = h // 4
            
            button_rect = self.get_button_rect()
            
            for attempt in range(20):
                x = random.uniform(margin_x, w - margin_x)
                y = random.uniform(margin_y, h - margin_y - 100)
                
                stimulus_area = QRectF(x - 75, y - 75, 150, 150)
                
                if not stimulus_area.intersects(button_rect):
                    self.stimulus_pos = QPointF(x, y)
                    break
            else:
                x = w / 2
                y = h / 2 - 100
                self.stimulus_pos = QPointF(x, y)
            
            self.timeout_timer = QTimer.singleShot(3000, self.timeout_reaction)
            
            if hasattr(self.parent, 'update'):
                self.parent.update()
        except RuntimeError as e:
            print(f"Объект был удален при показе стимула: {e}")
            return

    def timeout_reaction(self):
        if self.state == 'stimulus_shown':
            current_time = time.time()
            
            total_rt = 0
            latency = 0
            
            if self.stimulus_time:
                total_rt = max(0, current_time - self.stimulus_time)
                
                if self.has_left_button_area and self.release_time:
                    latency = max(0, self.release_time - self.stimulus_time)
            
            self.error_type = 'timeout'
            self.error_reason = 'Таймаут (3 секунды без реакции)'
            
            self._emit_result(
                latency=latency,
                motor_time=0,
                total_rt=total_rt,
                correct=False,
                anticipation=False,
                delay=True,
                click_pos=None,
                distance_from_center=None
            )

    def _emit_result(self, latency, motor_time, total_rt, correct, anticipation, delay, click_pos, distance_from_center):
        if self.timeout_timer:
            self.timeout_timer = None
        
        # Округляем время до 3 знаков после запятой
        latency = round(latency, 3)
        motor_time = round(motor_time, 3)
        total_rt = round(total_rt, 3)
        
        # Проверка на физическую реалистичность
        if latency < 0:
            latency = 0
        if motor_time < 0:
            motor_time = 0
        if total_rt < 0:
            total_rt = 0
        
        result = {
            'latency': latency,  # Время от стимула до покидания области кнопки
            'motor_time': motor_time,  # Время от покидания области кнопки до клика на стимуле
            'total_rt': total_rt,  # Общее время от стимула до клика
            'correct': correct,
            'anticipation': anticipation,
            'delay': delay,
            'click_x': round(click_pos.x(), 1) if click_pos else None,
            'click_y': round(click_pos.y(), 1) if click_pos else None,
            'distance_from_center': round(distance_from_center, 1) if distance_from_center else None,
            'error_type': self.error_type if not correct else 'none',
            'error_reason': self.error_reason if not correct else 'Успешная попытка'
        }
        
        # ДЕБАГ: Выводим результат
        print(f"DEBUG результат попытки:")
        print(f"  Правильно: {correct}")
        print(f"  Латентность: {latency:.3f} с")
        print(f"  Моторное: {motor_time:.3f} с")
        print(f"  Общее: {total_rt:.3f} с")
        print(f"  Тип ошибки: {self.error_type}")
        print(f"  Причина: {self.error_reason}")
        
        self.finished.emit(result)
        self.state = 'finished'
        
        try:
            if hasattr(self.parent, 'update'):
                self.parent.update()
        except RuntimeError:
            pass

    def stop_timers(self):
        self.timeout_timer = None
        self.stimulus_timer = None
        self.state = 'finished'