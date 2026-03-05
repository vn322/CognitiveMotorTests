# tests/size_discrimination.py (исправленная версия)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import random
import time
import math
from config import COLORS

class SizeDiscriminationTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.trial = 0
        self.max_trials = 10
        self.correct_count = 0
        self.circles = []
        self.target_circle = None
        self.target_radius = None
        self.start_time = None
        self.click_time = None
        self.difficulty = 1
        self.trial_difficulties = []
        self.trial_results = []
        self.button_rect = None
        self.size_biases = []
        self.selected_radii = []
        self.target_radii = []

    def get_button_rect(self):
        if not self.parent:
            return QRectF(0, 0, 160, 60)
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 100, 160, 60)

    def paint(self, painter):
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        painter.setPen(COLORS['text'])
        font = painter.font()
        font.setFamily("DejaVu Sans")
        font.setPointSize(12)
        painter.setFont(font)

        w = self.parent.width()
        h = self.parent.height()

        if self.state != 'finished':
            pressed = self.state in ('holding', 'trial')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Тест на различение размеров. Нажмите СТАРТ")
        elif self.state == 'trial':
            # Инструкция
            painter.drawText(QRectF(0, 20, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Найдите круг, наиболее близкий по размеру к образцу")
            
            # Образец размера
            if self.target_radius:
                # Рисуем образец
                painter.setBrush(QBrush(QColor(200, 200, 200)))  # Серый цвет для образца
                painter.setPen(QPen(COLORS['text'], 2))
                painter.drawEllipse(QPointF(w//2, 100), self.target_radius, self.target_radius)
                
                # Размер образца
                painter.drawText(QRectF(0, 60, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                               f"Образец: диаметр {int(self.target_radius * 2)}px")
            
            # Номер попытки
            painter.drawText(20, 150, f"Попытка: {self.trial}/{self.max_trials}")
            painter.drawText(20, 175, f"Правильных: {self.correct_count}/{self.trial-1}")
            
            # Информация о сложности
            difficulty_text = f"Сложность: {self.difficulty}"
            painter.drawText(w - 200, 150, difficulty_text)
            
            # Рисуем круги для выбора - ВСЕ ОДИНАКОВЫЕ ПО ЦВЕТУ!
            for circle in self.circles:
                px, py, radius, is_target = circle
                center = QPointF(px, py)
                
                # Все круги одинакового цвета (пастельный розовый)
                color = QColor(255, 179, 179)
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(COLORS['text'], 2))
                painter.drawEllipse(center, radius, radius)

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn'].darker(120) if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "СТАРТ")

    def generate_trial(self):
        """Создать испытание с кругами разного размера"""
        if not self.parent:
            return
        
        w, h = self.parent.width(), self.parent.height()
        
        # Очищаем предыдущие круги
        self.circles = []
        
        # Количество кругов
        num_circles = 4
        
        # Базовый размер (случайный в разумных пределах)
        self.target_radius = random.uniform(30, 70)
        self.target_radii.append(self.target_radius)
        
        # Определяем отклонение в зависимости от сложности
        # Чем выше сложность, тем меньше отклонение
        # Начинаем с маленьких различий для сложности 1
        max_deviation = 10 - (self.difficulty * 1.5)  # От 10px до 2.5px
        max_deviation = max(2, max_deviation)  # Минимальное отклонение 2px
        
        # Создаем позиции для кругов
        positions = []
        for _ in range(num_circles):
            for attempt in range(100):
                x = random.randint(100, w - 100)
                y = random.randint(250, h - 150)  # Смещаем ниже для образца
                pos = (x, y)
                
                # Проверяем, чтобы круги не перекрывались
                if all(math.sqrt((x - px)**2 + (y - py)**2) > 150 for px, py in positions):
                    positions.append(pos)
                    break
            else:
                positions.append((random.randint(100, w - 100), random.randint(250, h - 150)))
        
        # Определяем целевой круг (ближайший к образцу)
        target_idx = random.randint(0, num_circles - 1)
        
        # Создаем круги с контролируемыми отличиями
        for i, (px, py) in enumerate(positions):
            if i == target_idx:
                # Целевой круг (максимально близкий к образцу)
                deviation = random.uniform(-max_deviation * 0.2, max_deviation * 0.2)
                radius = self.target_radius + deviation
                is_target = True
            else:
                # Остальные круги - создаем плавно отличающиеся размеры
                # Используем распределение для плавных различий
                direction = 1 if random.random() < 0.5 else -1
                deviation_factor = random.uniform(0.3, 0.9)  # Плавное распределение
                deviation = max_deviation * deviation_factor * direction
                radius = self.target_radius + deviation
                is_target = False
            
            # Гарантируем разумные размеры
            radius = max(20, min(100, radius))
            
            self.circles.append((px, py, radius, is_target))
            self.target_circle = (px, py, radius, is_target) if is_target else self.target_circle

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.start_test()
        
        elif self.state == 'trial':
            click_pos = event.position()
            for circle in self.circles:
                px, py, radius, is_target = circle
                distance = math.sqrt((click_pos.x() - px)**2 + (click_pos.y() - py)**2)
                
                if distance <= radius:
                    self.click_time = time.time()
                    correct = is_target
                    
                    # Вычисляем отклонение (преувеличение/преуменьшение)
                    size_error = radius - self.target_radius
                    self.size_biases.append(size_error)
                    self.selected_radii.append(radius)
                    
                    # Записываем результат
                    reaction_time = self.click_time - self.start_time
                    self.trial_results.append({
                        'trial': self.trial,
                        'correct': correct,
                        'reaction_time': reaction_time,
                        'difficulty': self.difficulty,
                        'size_error': size_error,
                        'target_radius': self.target_radius,
                        'selected_radius': radius,
                        'absolute_error': abs(size_error)
                    })
                    
                    if correct:
                        self.correct_count += 1
                        # Увеличиваем сложность, но медленно
                        if self.difficulty < 5 and random.random() < 0.7:  # 70% шанс увеличения
                            self.difficulty += 1
                    else:
                        # Уменьшаем сложность, но не ниже 1
                        if self.difficulty > 1 and random.random() < 0.8:  # 80% шанс уменьшения
                            self.difficulty -= 1
                    
                    self.trial_difficulties.append(self.difficulty)
                    
                    # Переходим к следующему испытанию или завершаем
                    if self.trial >= self.max_trials:
                        self.finish_test()
                    else:
                        self.start_trial()
                    break

    def start_test(self):
        """Начать тест"""
        self.state = 'trial'
        self.trial = 0
        self.correct_count = 0
        self.difficulty = 1
        self.trial_difficulties = []
        self.trial_results = []
        self.size_biases = []
        self.selected_radii = []
        self.target_radii = []
        
        self.start_trial()

    def start_trial(self):
        """Начать новое испытание"""
        self.trial += 1
        self.generate_trial()
        self.start_time = time.time()
        
        if self.parent:
            self.parent.update()

    def finish_test(self):
        """Завершить тест"""
        # Рассчитываем среднее время реакции для правильных ответов
        correct_times = [r['reaction_time'] for r in self.trial_results if r['correct']]
        avg_reaction_time = sum(correct_times) / len(correct_times) if correct_times else 0
        
        # Точность
        accuracy = (self.correct_count / self.max_trials) * 100
        
        # Средняя сложность
        avg_difficulty = sum(self.trial_difficulties) / len(self.trial_difficulties) if self.trial_difficulties else 1
        
        # Анализ склонности к преувеличению/преуменьшению
        if self.size_biases:
            avg_size_error = sum(self.size_biases) / len(self.size_biases)
            avg_abs_error = sum(abs(b) for b in self.size_biases) / len(self.size_biases)
            
            # Определяем склонность
            if avg_size_error > 3:
                size_bias = "Склонность к преувеличению размеров"
                size_bias_type = "overestimation"
            elif avg_size_error < -3:
                size_bias = "Склонность к преуменьшению размеров"
                size_bias_type = "underestimation"
            else:
                size_bias = "Нейтральное восприятие размеров"
                size_bias_type = "neutral"
        else:
            avg_size_error = 0
            avg_abs_error = 0
            size_bias = "Нет данных"
            size_bias_type = "no_data"
        
        # Собираем все ошибки для детального анализа
        all_errors = [r['size_error'] for r in self.trial_results]
        absolute_errors = [abs(e) for e in all_errors]
        
        result = {
            'test_name': 'Различение размеров',
            'latency': 0,
            'motor_time': 0,
            'total_rt': avg_reaction_time,
            'correct': accuracy > 70,
            'correct_count': self.correct_count,
            'total_trials': self.max_trials,
            'accuracy': accuracy,
            'avg_reaction_time': avg_reaction_time,
            'avg_difficulty': avg_difficulty,
            'avg_size_error': avg_size_error,
            'avg_abs_size_error': avg_abs_error,
            'size_bias': size_bias,
            'size_bias_type': size_bias_type,
            'size_biases': self.size_biases,
            'all_errors': all_errors,
            'absolute_errors': absolute_errors,
            'selected_radii': self.selected_radii,
            'target_radii': self.target_radii,
            'trial_results': self.trial_results
        }
        
        self.finished.emit(result)
        self.state = 'finished'
        
        if self.parent:
            self.parent.update()

    def stop_timers(self):
        # В этом тесте нет активных таймеров
        pass