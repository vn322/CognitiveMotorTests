# tests/color_discrimination.py (исправленная версия)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import random
import time
import math
from config import COLORS

class ColorDiscriminationTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.trial = 0
        self.max_trials = 10
        self.correct_count = 0
        self.squares = []
        self.target_square = None
        self.target_color = None
        self.start_time = None
        self.click_time = None
        self.difficulty = 1
        self.trial_difficulties = []
        self.trial_results = []
        self.button_rect = None
        
        # Цвета для теста
        self.base_colors = [
            QColor(255, 100, 100),    # Красный
            QColor(100, 255, 100),    # Зеленый
            QColor(100, 100, 255),    # Синий
            QColor(255, 255, 100),    # Желтый
            QColor(255, 100, 255),    # Пурпурный
            QColor(100, 255, 255),    # Голубой
        ]

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
                           "Тест на различение цветов. Нажмите СТАРТ")
        elif self.state == 'trial':
            # Инструкция
            painter.drawText(QRectF(0, 20, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Найдите квадрат указанного цвета")
            
            # Целевой цвет
            if self.target_color:
                color_name = self.get_color_name(self.target_color)
                painter.drawText(QRectF(0, 60, w, 40), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                               f"Искомый цвет: {color_name}")
                
                # Показать целевой цвет
                painter.setBrush(QBrush(self.target_color))
                painter.setPen(QPen(COLORS['text'], 2))
                painter.drawRect(w//2 - 25, 90, 50, 50)
            
            # Номер попытки
            painter.drawText(20, 150, f"Попытка: {self.trial}/{self.max_trials}")
            painter.drawText(20, 175, f"Правильных: {self.correct_count}/{self.trial-1}")
            
            # Информация о сложности
            difficulty_text = f"Сложность: {self.difficulty}"
            painter.drawText(w - 200, 150, difficulty_text)
            
            # Рисуем квадраты
            for square in self.squares:
                px, py, color, is_target = square
                center = QPointF(px, py)
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(COLORS['text'], 2))
                
                size = 60
                painter.drawRect(QRectF(px - size/2, py - size/2, size, size))

    def get_color_name(self, color):
        """Получить название цвета"""
        if color == QColor(255, 100, 100):
            return "Красный"
        elif color == QColor(100, 255, 100):
            return "Зеленый"
        elif color == QColor(100, 100, 255):
            return "Синий"
        elif color == QColor(255, 255, 100):
            return "Желтый"
        elif color == QColor(255, 100, 255):
            return "Пурпурный"
        elif color == QColor(100, 255, 255):
            return "Голубой"
        return ""

    def draw_start_button(self, painter, pressed=False):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn'].darker(120) if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 15, 15)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "СТАРТ")

    def generate_trial(self):
        """Создать испытание с квадратами разного цвета"""
        if not self.parent:
            return
        
        w, h = self.parent.width(), self.parent.height()
        
        # Очищаем предыдущие квадраты
        self.squares = []
        
        # Количество квадратов
        num_squares = 4
        
        # Выбираем базовый цвет
        self.target_color = random.choice(self.base_colors)
        
        # Создаем позиции для квадратов
        positions = []
        for _ in range(num_squares):
            for attempt in range(100):
                x = random.randint(100, w - 100)
                y = random.randint(200, h - 150)
                pos = (x, y)
                
                # Проверяем, чтобы квадраты не перекрывались
                if all(math.sqrt((x - px)**2 + (y - py)**2) > 100 for px, py in positions):
                    positions.append(pos)
                    break
            else:
                positions.append((random.randint(100, w - 100), random.randint(200, h - 150)))
        
        # Определяем целевой квадрат
        target_idx = random.randint(0, num_squares - 1)
        
        # Создаем квадраты
        for i, (px, py) in enumerate(positions):
            if i == target_idx:
                # Целевой квадрат (точный цвет)
                color = self.target_color
                is_target = True
            else:
                # Остальные квадраты (похожие цвета)
                color = self.generate_similar_color(self.target_color, self.difficulty)
                is_target = False
            
            self.squares.append((px, py, color, is_target))

    def generate_similar_color(self, base_color, difficulty):
        """Создать похожий цвет (чем выше сложность, тем больше похожесть)"""
        r, g, b = base_color.red(), base_color.green(), base_color.blue()
        
        # Чем выше сложность, тем меньше отклонение
        max_deviation = 100 - (difficulty * 15)
        max_deviation = max(20, max_deviation)  # Минимальное отклонение
        
        r_new = random.randint(max(0, r - max_deviation), min(255, r + max_deviation))
        g_new = random.randint(max(0, g - max_deviation), min(255, g + max_deviation))
        b_new = random.randint(max(0, b - max_deviation), min(255, b + max_deviation))
        
        return QColor(r_new, g_new, b_new)

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.start_test()
        
        elif self.state == 'trial':
            click_pos = event.position()
            for square in self.squares:
                px, py, color, is_target = square
                size = 60
                
                if (abs(click_pos.x() - px) <= size/2 and 
                    abs(click_pos.y() - py) <= size/2):
                    
                    self.click_time = time.time()
                    correct = is_target
                    
                    # Записываем результат
                    reaction_time = self.click_time - self.start_time
                    self.trial_results.append({
                        'trial': self.trial,
                        'correct': correct,
                        'reaction_time': reaction_time,
                        'difficulty': self.difficulty
                    })
                    
                    if correct:
                        self.correct_count += 1
                        # Увеличиваем сложность
                        if self.difficulty < 5:
                            self.difficulty += 1
                    else:
                        # Уменьшаем сложность, но не ниже 1
                        if self.difficulty > 1:
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
        
        result = {
            'test_name': 'Различение цветов',
            'latency': 0,
            'motor_time': 0,
            'total_rt': avg_reaction_time,
            'correct': accuracy > 70,
            'correct_count': self.correct_count,
            'total_trials': self.max_trials,
            'accuracy': accuracy,
            'avg_reaction_time': avg_reaction_time,
            'avg_difficulty': avg_difficulty,
            'trial_results': self.trial_results
        }
        
        self.finished.emit(result)
        self.state = 'finished'
        
        if self.parent:
            self.parent.update()

    def stop_timers(self):
        # В этом тесте нет активных таймеров
        pass