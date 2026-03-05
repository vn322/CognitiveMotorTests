# tests/complex_choice.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
import time
import random
from config import COLORS

class ComplexChoiceTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.stimulus_time = None
        self.release_time = None  # Время покидания курсором области кнопки "Старт"
        self.click_time = None    # Время клика на стимуле
        self.stimuli = []
        self.sample_shape = None
        self.sample_color = None
        self.click_pos = None
        self.button_rect = None
        self.timeout_timer = None
        self.stimulus_timer = None
        self.has_left_button_area = False  # Флаг покидания области кнопки "Старт"
        self.error_type = None
        self.error_reason = None

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
            pressed = self.state in ('holding', 'stimulus_shown')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                             "Запомните образец. Нажмите и удерживайте «Старт», затем выберите точную копию.")
        elif self.state == 'stimulus_shown':
            self.draw_stimuli(painter)

    def draw_sample(self, painter):
        sample_x, sample_y = 20, 20
        if self.state == 'waiting_start':
            self.sample_shape = random.choice(['circle', 'square', 'triangle'])
            self.sample_color = random.choice([
                QColor(255, 179, 186),  # red
                QColor(181, 234, 215),  # green
                QColor(255, 224, 179),  # yellow
                QColor(199, 206, 234),  # blue
                QColor(230, 190, 255),  # purple
                QColor(255, 200, 200)   # pink
            ])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.sample_color))
        size = 40
        rect = QRectF(sample_x, sample_y, size, size)
        if self.sample_shape == 'circle':
            painter.drawEllipse(rect)
        elif self.sample_shape == 'square':
            painter.drawRect(rect)
        elif self.sample_shape == 'triangle':
            # Рисуем треугольник
            points = [
                QPointF(sample_x + size/2, sample_y),
                QPointF(sample_x, sample_y + size),
                QPointF(sample_x + size, sample_y + size)
            ]
            painter.drawPolygon(points)

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn_pressed'] if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "Старт")

    def draw_stimuli(self, painter):
        for stim in self.stimuli:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(stim['color']))
            x, y = stim['pos'].x(), stim['pos'].y()
            size = 60
            rect = QRectF(x - size/2, y - size/2, size, size)
            if stim['shape'] == 'circle':
                painter.drawEllipse(rect)
            elif stim['shape'] == 'square':
                painter.drawRect(rect)
            elif stim['shape'] == 'triangle':
                # Рисуем треугольник
                points = [
                    QPointF(x, y - size/2),
                    QPointF(x - size/2, y + size/2),
                    QPointF(x + size/2, y + size/2)
                ]
                painter.drawPolygon(points)

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
                self.error_type = None
                self.error_reason = None
                self.parent.update()
                delay = random.uniform(0.5, 2.0)
                self.stimulus_timer = QTimer.singleShot(int(delay * 1000), self.show_stimuli)
        
        elif self.state == 'stimulus_shown':
            # Это клик на одном из стимулов
            self.click_time = time.time()
            self.click_pos = event.position()
            
            # Проверяем, на какой стимул кликнули
            clicked_stimulus = None
            dist = None
            
            for stim in self.stimuli:
                # Область клика на стимуле
                stim_rect = QRectF(stim['pos'].x() - 50, stim['pos'].y() - 50, 100, 100)
                if stim_rect.contains(event.position()):
                    clicked_stimulus = stim
                    # Расстояние от клика до центра стимула
                    dx = event.position().x() - stim['pos'].x()
                    dy = event.position().y() - stim['pos'].y()
                    dist = (dx * dx + dy * dy) ** 0.5  # Евклидово расстояние
                    break
            
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
                    
                    if clicked_stimulus is not None:
                        # Кликнули на каком-то стимуле
                        if clicked_stimulus['is_target']:
                            # Кликнули на правильный (целевой) стимул
                            correct = True
                            self.error_type = 'none'
                            self.error_reason = 'Успешная попытка'
                            
                            # ДЕБАГ: Выводим временные метки
                            print(f"DEBUG успешная попытка (Сложный выбор):")
                            print(f"  Показан стимул: {self.stimulus_time:.3f}")
                            print(f"  Покинул область кнопки: {self.release_time:.3f}")
                            print(f"  Кликнул: {self.click_time:.3f}")
                            print(f"  Латентность: {latency:.3f} сек ({latency*1000:.0f} мс)")
                            print(f"  Моторное время: {motor_time:.3f} сек ({motor_time*1000:.0f} мс)")
                            print(f"  Общее время: {total_rt:.3f} сек ({total_rt*1000:.0f} мс)")
                            print(f"  Расстояние: {dist:.1f}px")
                        else:
                            # Кликнули на неправильный стимул (дистрактор)
                            correct = False
                            self.error_type = 'wrong_choice'
                            self.error_reason = 'Выбран неверный стимул (дистрактор)'
                    else:
                        # Промах (кликнул мимо всех стимулов)
                        correct = False
                        self.error_type = 'miss'
                        self.error_reason = 'Промах (клин мимо стимулов)'
                else:
                    # Не покинул область кнопки перед кликом
                    correct = False
                    if clicked_stimulus is not None:
                        if clicked_stimulus['is_target']:
                            self.error_type = 'no_release_correct'
                            self.error_reason = 'Кликнул на правильном стимуле, не покинув область кнопки'
                        else:
                            self.error_type = 'no_release_wrong'
                            self.error_reason = 'Кликнул на неверном стимуле, не покинув область кнопки'
                    else:
                        self.error_type = 'no_release_miss'
                        self.error_reason = 'Не покинул область кнопки и кликнул мимо стимулов'
                    
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
                    distance_from_center=dist,
                    target_shape=self.sample_shape,
                    target_color_info=self._color_to_str(self.sample_color)
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
                    self.error_reason = 'Покинул область кнопки до появления стимулов'
                    
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
                        distance_from_center=None,
                        target_shape=self.sample_shape,
                        target_color_info=self._color_to_str(self.sample_color)
                    )

    def show_stimuli(self):
        try:
            if not self.parent or not hasattr(self.parent, 'width'):
                return
                
            if self.state != 'holding':
                return
                
            self.state = 'stimulus_shown'
            self.stimulus_time = time.time()
            
            # Создаем стимулы (3 стимула: 1 целевой + 2 дистрактора)
            shapes = ['circle', 'square', 'triangle']
            colors = [
                QColor(255, 179, 186),  # red
                QColor(181, 234, 215),  # green
                QColor(255, 224, 179),  # yellow
                QColor(199, 206, 234),  # blue
                QColor(230, 190, 255),  # purple
                QColor(255, 200, 200)   # pink
            ]
            target_shape = self.sample_shape
            target_color = self.sample_color

            w, h = self.parent.width(), self.parent.height()
            positions = []
            for _ in range(3):  # 3 стимула: 1 целевой + 2 дистрактора
                for _ in range(100):
                    x = random.uniform(100, w - 100)
                    y = random.uniform(100, h - 150)
                    pos = QPointF(x, y)
                    
                    # Проверяем, чтобы стимул не пересекался с кнопкой "Старт"
                    btn_rect = self.get_button_rect()
                    stim_rect = QRectF(x - 50, y - 50, 100, 100)
                    
                    if (all((pos - p).manhattanLength() > 120 for p in positions) and 
                        not stim_rect.intersects(btn_rect)):
                        positions.append(pos)
                        break
                else:
                    # Если не удалось найти подходящую позицию
                    x = w / 2 + random.uniform(-100, 100)
                    y = h / 2 - 50 + random.uniform(-50, 50)
                    positions.append(QPointF(x, y))

            random.shuffle(positions)

            self.stimuli = []
            # Целевой стимул (полное совпадение с образцом)
            self.stimuli.append({
                'pos': positions[0],
                'is_target': True,
                'shape': target_shape,
                'color': target_color
            })

            # Дистрактор 1: отличается только формой
            shape1 = random.choice([s for s in shapes if s != target_shape])
            self.stimuli.append({
                'pos': positions[1],
                'is_target': False,
                'shape': shape1,
                'color': target_color  # Цвет как у цели
            })

            # Дистрактор 2: отличается только цветом
            color2 = random.choice([c for c in colors if c != target_color])
            self.stimuli.append({
                'pos': positions[2],
                'is_target': False,
                'shape': target_shape,  # Форма как у цели
                'color': color2
            })

            self.timeout_timer = QTimer.singleShot(3000, self.timeout_reaction)
            
            if hasattr(self.parent, 'update'):
                self.parent.update()
                
        except RuntimeError as e:
            print(f"Объект был удален при показе стимулов: {e}")
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
                distance_from_center=None,
                target_shape=self.sample_shape,
                target_color_info=self._color_to_str(self.sample_color)
            )

    def _color_to_str(self, color):
        """Преобразовать цвет в строку для отчета"""
        # Получаем значения RGBA цвета
        if not color:
            return 'неизвестный'
            
        r = color.red()
        g = color.green()
        b = color.blue()
        
        # Сравниваем с известными цветами
        if r == 255 and g == 179 and b == 186:
            return 'красный'
        elif r == 181 and g == 234 and b == 215:
            return 'зеленый'
        elif r == 255 and g == 224 and b == 179:
            return 'желтый'
        elif r == 199 and g == 206 and b == 234:
            return 'синий'
        elif r == 230 and g == 190 and b == 255:
            return 'фиолетовый'
        elif r == 255 and g == 200 and b == 200:
            return 'розовый'
        else:
            return f'цвет({r},{g},{b})'

    def _emit_result(self, latency, motor_time, total_rt, correct, anticipation, delay, 
                    click_pos, distance_from_center, target_shape, target_color_info):
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
            'error_reason': self.error_reason if not correct else 'Успешная попытка',
            'target_shape': target_shape,
            'target_color_info': target_color_info,
            'total_stimuli': len(self.stimuli)
        }
        
        # ДЕБАГ: Выводим результат
        print(f"DEBUG результат попытки (Сложный выбор):")
        print(f"  Правильно: {correct}")
        print(f"  Целевая форма: {target_shape}")
        print(f"  Целевой цвет: {target_color_info}")
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