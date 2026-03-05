# tests/attention_switching.py (исправленная версия)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import time
import random
import math
from config import COLORS

class AttentionSwitchingTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.current_rule = 'click_circles'  # Начинаем всегда с кругов
        self.rule_changed_time = None
        self.click_time = None
        self.current_trial = 0
        self.total_trials = 16
        self.correct_count = 0
        self.reaction_times = []
        self.rule_switch_trial = 8
        self.has_switched = False
        self.stimuli = []
        self.target_shape = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_next_stimulus)
        self.timeout_timer = None
        self.button_rect = None
        self.feedback_timer = None
        self.show_feedback = False
        self.feedback_correct = False
        self.feedback_message = ""
        self.trial_results = []
        self.grid_size = 4
        self.figures_per_trial = 6
        # Упрощенная палитра цветов для лучшего восприятия
        self.colors = [
            QColor(100, 150, 255),  # Пастельный синий
            QColor(255, 150, 150),  # Пастельный розовый
            QColor(150, 255, 150),  # Пастельный зеленый
            QColor(255, 255, 150),  # Пастельный желтый
            QColor(255, 200, 100),  # Пастельный оранжевый
            QColor(200, 150, 255),  # Пастельный фиолетовый
        ]

    def get_button_rect(self):
        if not self.parent:
            return QRectF(0, 0, 160, 60)
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 100, 160, 60)

    def paint(self, painter):
        if not self.parent:
            return
            
        w, h = self.parent.width(), self.parent.height()
        
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        painter.setPen(COLORS['text'])
        
        font = QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(11)
        painter.setFont(font)

        if self.state != 'finished' and self.state != 'showing_feedback':
            pressed = self.state in ('holding', 'running')
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Тест на переключение внимания - Нажмите СТАРТ")
        
        elif self.state == 'running':
            # Отрисовка фона информации
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, w, 120)
            
            # Текущее правило
            rule_text = f"Правило: {self.get_rule_text()}"
            painter.setPen(COLORS['text'])
            painter.drawText(QRectF(0, 20, w, 30), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, rule_text)
            
            # Что нужно кликать
            target_text = f"Кликайте на: {self.get_target_shape_text()}"
            painter.drawText(QRectF(0, 45, w, 30), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, target_text)
            
            # Прогресс
            progress_text = f"Испытание: {self.current_trial}/{self.total_trials}"
            painter.drawText(20, 75, progress_text)
            
            # Правильных ответов
            accuracy = (self.correct_count / self.current_trial * 100) if self.current_trial > 0 else 0
            painter.drawText(20, 95, f"Точность: {accuracy:.1f}%")
            
            # Индикатор переключения
            if self.has_switched:
                painter.setPen(QColor(255, 140, 0))
                painter.drawText(QRectF(0, 110, w, 30), 
                               Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                               "ПРАВИЛО ИЗМЕНИЛОСЬ!")
            
            # Отрисовка всех фигур - ВСЕ ОДИНАКОВЫЕ
            for stimulus in self.stimuli:
                self.draw_stimulus(painter, stimulus)
        
        elif self.state == 'showing_feedback':
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, w, h)
            
            feedback_width = 300
            feedback_height = 150
            feedback_x = int((w - feedback_width) / 2)
            feedback_y = int((h - feedback_height) / 2)
            
            if self.feedback_correct:
                bg_color = QColor(200, 255, 200, 230)
                text_color = QColor(0, 100, 0)
                symbol = "✓"
            else:
                bg_color = QColor(255, 200, 200, 230)
                text_color = QColor(150, 0, 0)
                symbol = "✗"
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(text_color, 2))
            painter.drawRoundedRect(feedback_x, feedback_y, feedback_width, feedback_height, 15, 15)
            
            font.setPointSize(36)
            painter.setFont(font)
            painter.setPen(text_color)
            painter.drawText(QRectF(feedback_x, feedback_y + 20, feedback_width, 50),
                           Qt.AlignmentFlag.AlignCenter, symbol)
            
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(QRectF(feedback_x, feedback_y + 80, feedback_width, 40),
                           Qt.AlignmentFlag.AlignCenter, self.feedback_message)
            
            font.setPointSize(11)
            painter.setFont(font)
            painter.drawText(QRectF(feedback_x, feedback_y + 120, feedback_width, 30),
                           Qt.AlignmentFlag.AlignCenter, "Нажмите для продолжения")

    def draw_stimulus(self, painter, stimulus):
        """Отрисовка стимула - ВСЕ ФИГУРЫ ВЫГЛЯДЯТ ОДИНАКОВО"""
        x, y, shape, color, is_target = stimulus
        
        # ВСЕ фигуры рисуются одинаково, независимо от того, целевые они или нет
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if shape == 'circle':
            radius = 35
            painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
        elif shape == 'square':
            size = 70
            painter.drawRect(QRectF(x - size/2, y - size/2, size, size))
        
        # Контур для ВСЕХ фигур одинаковый - тонкий светлый
        painter.setPen(QPen(QColor(100, 100, 100, 100), 1))  # Полупрозрачный серый
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        if shape == 'circle':
            painter.drawEllipse(QRectF(x - 35, y - 35, 70, 70))
        elif shape == 'square':
            painter.drawRect(QRectF(x - 35, y - 35, 70, 70))

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

    def get_rule_text(self):
        if self.current_rule == 'click_circles':
            return "КЛИКАЙТЕ НА КРУГИ"
        elif self.current_rule == 'click_squares':
            return "КЛИКАЙТЕ НА КВАДРАТЫ"
        return ""

    def get_target_shape_text(self):
        if self.current_rule == 'click_circles':
            return "КРУГИ"
        elif self.current_rule == 'click_squares':
            return "КВАДРАТЫ"
        return ""

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.start_test()
        
        elif self.state == 'running' and self.stimuli:
            click_pos = event.position()
            
            clicked_target = False
            for stimulus in self.stimuli:
                x, y, shape, color, is_target = stimulus
                
                if shape == 'circle':
                    distance = math.hypot(click_pos.x() - x, click_pos.y() - y)
                    clicked = distance <= 35
                else:
                    clicked = (abs(click_pos.x() - x) <= 35 and abs(click_pos.y() - y) <= 35)
                
                if clicked:
                    self.process_click(is_target, shape)
                    clicked_target = True
                    break
            
            if not clicked_target:
                self.process_click(False, None)
        
        elif self.state == 'showing_feedback':
            self.state = 'running'
            self.show_feedback = False
            self.show_next_stimulus()

    def start_test(self):
        print("=" * 50)
        print("НАЧАЛО ТЕСТА НА ПЕРЕКЛЮЧЕНИЕ ВНИМАНИЯ")
        print("Теперь на экране будут КРУГИ и КВАДРАТЫ")
        print("Вам нужно кликать только на указанные фигуры")
        print("ПОМНИТЕ: все фигуры выглядят одинаково!")
        print("Определяйте форму по контуру фигуры")
        print("=" * 50)
        
        self.state = 'running'
        self.start_time = time.time()
        self.current_rule = 'click_circles'
        self.current_trial = 0
        self.correct_count = 0
        self.reaction_times = []
        self.trial_results = []
        self.has_switched = False
        
        if self.parent:
            self.parent.update()
        
        QTimer.singleShot(1000, self.show_next_stimulus)

    def show_next_stimulus(self):
        if not self.parent:
            return
            
        if self.current_trial >= self.total_trials:
            self.finish_test()
            return
        
        self.current_trial += 1
        
        if self.current_trial > self.rule_switch_trial and not self.has_switched:
            self.switch_rule()
        
        w, h = self.parent.width(), self.parent.height()
        
        target_shape = 'circle' if self.current_rule == 'click_circles' else 'square'
        distractor_shape = 'square' if target_shape == 'circle' else 'circle'
        
        self.stimuli = []
        
        cell_width = w / (self.grid_size + 2)
        cell_height = (h - 150) / (self.grid_size + 2)
        
        positions = []
        for i in range(1, self.grid_size + 1):
            for j in range(1, self.grid_size + 1):
                x = cell_width * i + cell_width / 2
                y = cell_height * j + 80
                positions.append((x, y))
        
        random.shuffle(positions)
        
        num_targets = random.randint(1, 2)
        num_distractors = self.figures_per_trial - num_targets
        
        # Добавляем целевые фигуры - цвета случайные, но одинаковые для всех фигур
        for i in range(num_targets):
            if positions:
                x, y = positions.pop()
                color = random.choice(self.colors)  # Случайный цвет
                self.stimuli.append((x, y, target_shape, color, True))
        
        # Добавляем отвлекающие фигуры - тоже случайные цвета
        for i in range(num_distractors):
            if positions:
                x, y = positions.pop()
                color = random.choice(self.colors)  # Случайный цвет
                self.stimuli.append((x, y, distractor_shape, color, False))
        
        # Перемешиваем фигуры, чтобы целевые и отвлекающие были в случайном порядке
        random.shuffle(self.stimuli)
        
        self.stimulus_time = time.time()
        
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.timeout_stimulus)
        self.timeout_timer.start(3000)
        
        print(f"Испытание {self.current_trial}: Правило - {self.current_rule}")
        print(f"  На экране: {num_targets} целевых {target_shape}, {num_distractors} отвлекающих {distractor_shape}")
        
        if self.parent:
            self.parent.update()

    def switch_rule(self):
        self.has_switched = True
        if self.current_rule == 'click_circles':
            self.current_rule = 'click_squares'
        else:
            self.current_rule = 'click_circles'
        
        self.rule_changed_time = time.time()
        
        print("=" * 50)
        print(f"ПРАВИЛО ИЗМЕНИЛОСЬ!")
        print(f"Теперь нужно кликать на: {self.get_target_shape_text()}")
        print("=" * 50)

    def process_click(self, clicked_on_target, clicked_shape):
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        
        click_time = time.time()
        reaction_time = click_time - self.stimulus_time
        self.reaction_times.append(reaction_time)
        
        correct = clicked_on_target
        
        if correct:
            self.correct_count += 1
            self.feedback_message = "Правильно! Это целевая фигура"
            print(f"Испытание {self.current_trial}: ✓ Правильно! Время: {reaction_time:.3f} с")
        else:
            if clicked_shape is None:
                self.feedback_message = "Промах! Кликните по фигуре"
                print(f"Испытание {self.current_trial}: ✗ Промах! Кликните по фигурам")
            else:
                self.feedback_message = f"Неправильно! Это не {self.get_target_shape_text()}"
                print(f"Испытание {self.current_trial}: ✗ Неправильно! Время: {reaction_time:.3f} с")
        
        self.trial_results.append({
            'trial': self.current_trial,
            'correct': correct,
            'reaction_time': reaction_time,
            'rule': self.current_rule,
            'rule_changed': self.has_switched,
            'clicked_on_target': clicked_on_target
        })
        
        self.show_feedback = True
        self.feedback_correct = correct
        self.state = 'showing_feedback'
        
        self.feedback_timer = QTimer()
        self.feedback_timer.setSingleShot(True)
        self.feedback_timer.timeout.connect(self.continue_after_feedback)
        self.feedback_timer.start(800)

    def continue_after_feedback(self):
        if not self.parent:
            return
            
        if self.state == 'showing_feedback':
            self.state = 'running'
            self.show_feedback = False
            QTimer.singleShot(100, self.show_next_stimulus)

    def timeout_stimulus(self):
        print(f"Испытание {self.current_trial}: ТАЙМАУТ - не успел")
        
        self.trial_results.append({
            'trial': self.current_trial,
            'correct': False,
            'reaction_time': 3.0,
            'rule': self.current_rule,
            'rule_changed': self.has_switched,
            'clicked_on_target': False,
            'timeout': True
        })
        
        self.show_feedback = True
        self.feedback_correct = False
        self.feedback_message = "Время вышло! Будьте быстрее"
        self.state = 'showing_feedback'
        
        if self.parent:
            self.parent.update()
        
        QTimer.singleShot(500, self.show_next_stimulus)

    def finish_test(self):
        print("=" * 50)
        print("ТЕСТ ЗАВЕРШЕН")
        
        pre_switch_results = [r for r in self.trial_results if not r['rule_changed']]
        post_switch_results = [r for r in self.trial_results if r['rule_changed']]
        
        correct_reaction_times = [r['reaction_time'] for r in self.trial_results if r['correct']]
        
        if correct_reaction_times:
            avg_rt = sum(correct_reaction_times) / len(correct_reaction_times)
        else:
            avg_rt = 0
        
        accuracy = (self.correct_count / self.total_trials) * 100
        
        pre_switch_correct = [r['reaction_time'] for r in pre_switch_results if r['correct']]
        post_switch_correct = [r['reaction_time'] for r in post_switch_results if r['correct']]
        
        avg_pre = sum(pre_switch_correct) / len(pre_switch_correct) if pre_switch_correct else 0
        avg_post = sum(post_switch_correct) / len(post_switch_correct) if post_switch_correct else 0
        switch_cost = avg_post - avg_pre
        
        print(f"Всего испытаний: {self.total_trials}")
        print(f"Правильных: {self.correct_count} ({accuracy:.1f}%)")
        print(f"Среднее время правильных ответов: {avg_rt:.3f} с")
        print(f"Время до переключения: {avg_pre:.3f} с ({len(pre_switch_correct)} попыток)")
        print(f"Время после переключения: {avg_post:.3f} с ({len(post_switch_correct)} попыток)")
        print(f"Стоимость переключения: {switch_cost:.3f} с")
        print("=" * 50)
        
        self._emit_result(
            latency=0,
            motor_time=0,
            total_rt=avg_rt,
            correct_count=self.correct_count,
            total_trials=self.total_trials,
            accuracy=accuracy,
            avg_pre_switch=avg_pre,
            avg_post_switch=avg_post,
            switch_cost=switch_cost,
            rule_changed=self.has_switched,
            trial_results=self.trial_results
        )

    def _emit_result(self, **kwargs):
        self.stop_timers()
        
        result = {
            'test_name': 'Переключение внимания',
            'latency': kwargs.get('latency', 0),
            'motor_time': kwargs.get('motor_time', 0),
            'total_rt': kwargs.get('total_rt', 0),
            'correct': kwargs.get('correct_count', 0) > 0,
            'correct_count': kwargs.get('correct_count', 0),
            'total_trials': kwargs.get('total_trials', 0),
            'accuracy': kwargs.get('accuracy', 0),
            'avg_pre_switch': kwargs.get('avg_pre_switch', 0),
            'avg_post_switch': kwargs.get('avg_post_switch', 0),
            'switch_cost': kwargs.get('switch_cost', 0),
            'rule_changed': kwargs.get('rule_changed', False),
            'trial_results': kwargs.get('trial_results', [])
        }
        
        self.finished.emit(result)
        self.state = 'finished'

    def stop_timers(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.timeout_timer and self.timeout_timer.isActive():
            self.timeout_timer.stop()
        if self.feedback_timer and self.feedback_timer.isActive():
            self.feedback_timer.stop()