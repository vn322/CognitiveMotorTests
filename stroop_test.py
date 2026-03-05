# tests/stroop_test.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import time
import random
from config import COLORS

class StroopTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.trials = []
        self.current_trial = 0
        self.total_trials = 20
        self.correct_count = 0
        self.reaction_times = []
        self.button_rect = None
        self.timer = QTimer()
        self.stimulus_time = None
        self.current_word = ""
        self.current_color = ""
        self.current_task = ""  # "word" или "color"
        self.feedback_duration = 500
        self.show_feedback = False
        self.feedback_correct = False
        self.feedback_message = ""
        
        # Цвета для теста Струпа
        self.colors = {
            'красный': QColor(255, 100, 100),
            'синий': QColor(100, 100, 255),
            'зеленый': QColor(100, 200, 100),
            'желтый': QColor(255, 255, 100),
            'фиолетовый': QColor(200, 100, 255)
        }
        
        self.color_names = list(self.colors.keys())

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

        if self.state != 'finished' and self.state != 'showing_feedback':
            pressed = self.state == 'holding'
            self.draw_start_button(painter, pressed=pressed)

        if self.state == 'waiting_start':
            painter.drawText(QRectF(0, 0, w, 40), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           "Тест Струпа - Нажмите СТАРТ")
            
            explanation = "Читайте слово или называйте цвет в зависимости от инструкции"
            painter.drawText(QRectF(0, 50, w, 40), 
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                           explanation)
        
        elif self.state == 'running':
            # Информация
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, w, 80)
            
            painter.setPen(COLORS['text'])
            painter.drawText(20, 30, f"Испытание: {self.current_trial}/{self.total_trials}")
            painter.drawText(20, 55, f"Правильных: {self.correct_count}")
            
            # Задача
            if self.current_task:
                task_text = "ЧИТАЙТЕ СЛОВО" if self.current_task == "word" else "НАЗЫВАЙТЕ ЦВЕТ"
                painter.drawText(QRectF(0, 70, w, 30), 
                               Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                               task_text)
            
            # Отображение стимула
            if self.current_word and self.current_color:
                center_x = w / 2
                center_y = h / 2
                
                # Слово
                font.setPointSize(36)
                painter.setFont(font)
                
                # Получаем цвет для отображения
                display_color = self.colors.get(self.current_color, COLORS['text'])
                painter.setPen(display_color)
                
                painter.drawText(QRectF(0, center_y - 50, w, 100),
                               Qt.AlignmentFlag.AlignCenter, self.current_word)
                
                # Кнопки выбора
                self.draw_choice_buttons(painter, w, h)
        
        elif self.state == 'showing_feedback':
            # Полупрозрачный фон
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, w, h)
            
            # Окно обратной связи
            feedback_width = 300
            feedback_height = 150
            feedback_x = int((w - feedback_width) / 2)
            feedback_y = int((h - feedback_height) / 2)
            
            # Цвет фона
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
            
            # Текст обратной связи
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

    def draw_choice_buttons(self, painter, w, h):
        """Отрисовка кнопок выбора цвета"""
        button_width = 100
        button_height = 50
        button_spacing = 20
        total_width = len(self.color_names) * button_width + (len(self.color_names) - 1) * button_spacing
        start_x = (w - total_width) / 2
        
        for i, color_name in enumerate(self.color_names):
            x = start_x + i * (button_width + button_spacing)
            y = h - 150
            
            # Кнопка
            color = self.colors[color_name]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(COLORS['text'], 2))
            painter.drawRoundedRect(int(x), int(y), button_width, button_height, 10, 10)
            
            # Текст
            painter.setPen(COLORS['text'])
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(QRectF(x, y, button_width, button_height),
                           Qt.AlignmentFlag.AlignCenter, color_name)

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
        
        elif self.state == 'running' and self.current_word:
            self.handle_choice_click(event.position())
        
        elif self.state == 'showing_feedback':
            self.state = 'running'
            self.show_feedback = False
            self.show_next_stimulus()

    def start_test(self):
        """Начать тест"""
        print("=" * 50)
        print("НАЧАЛО ТЕСТА СТРУПА")
        print("=" * 50)
        
        self.state = 'running'
        self.start_time = time.time()
        self.current_trial = 0
        self.correct_count = 0
        self.reaction_times = []
        
        # Генерируем испытания
        self.generate_trials()
        
        self.show_next_stimulus()

    def generate_trials(self):
        """Генерация испытаний"""
        self.trials = []
        
        # Создаем конфликтные и неконфликтные испытания
        for i in range(self.total_trials):
            # Случайное слово
            word = random.choice(self.color_names)
            
            # Случайный цвет (может совпадать или не совпадать со словом)
            color = random.choice(self.color_names)
            
            # Случайная задача
            task = random.choice(["word", "color"])
            
            self.trials.append({
                'word': word,
                'color': color,
                'task': task,
                'congruent': word == color  # Конгруэнтное или нет
            })

    def show_next_stimulus(self):
        """Показать следующий стимул"""
        if self.current_trial >= self.total_trials:
            self.finish_test()
            return
        
        trial = self.trials[self.current_trial]
        self.current_word = trial['word']
        self.current_color = trial['color']
        self.current_task = trial['task']
        
        self.stimulus_time = time.time()
        self.current_trial += 1
        
        print(f"Испытание {self.current_trial}: слово='{self.current_word}', "
              f"цвет='{self.current_color}', задача='{self.current_task}'")
        
        if self.parent:
            self.parent.update()

    def handle_choice_click(self, click_pos):
        """Обработка выбора цвета"""
        w, h = self.parent.width(), self.parent.height()
        button_width = 100
        button_height = 50
        button_spacing = 20
        total_width = len(self.color_names) * button_width + (len(self.color_names) - 1) * button_spacing
        start_x = (w - total_width) / 2
        
        # Проверяем, в какую кнопку кликнули
        for i, color_name in enumerate(self.color_names):
            x = start_x + i * (button_width + button_spacing)
            y = h - 150
            
            if (x <= click_pos.x() <= x + button_width and 
                y <= click_pos.y() <= y + button_height):
                
                self.process_choice(color_name)
                break

    def process_choice(self, chosen_color):
        """Обработка выбранного цвета"""
        click_time = time.time()
        reaction_time = click_time - self.stimulus_time
        self.reaction_times.append(reaction_time)
        
        # Определяем правильный ответ
        if self.current_task == "word":
            correct_answer = self.current_word
        else:  # "color"
            correct_answer = self.current_color
        
        correct = (chosen_color == correct_answer)
        
        if correct:
            self.correct_count += 1
            self.feedback_message = "Правильно!"
            print(f"✓ Правильно! Выбрано: {chosen_color}, задача: {self.current_task}")
        else:
            self.feedback_message = f"Неправильно! Нужно: {correct_answer}"
            print(f"✗ Неправильно! Выбрано: {chosen_color}, нужно: {correct_answer}")
        
        # Показываем обратную связь
        self.show_feedback = True
        self.feedback_correct = correct
        self.state = 'showing_feedback'
        
        # Автоматическое продолжение
        QTimer.singleShot(800, self.continue_after_feedback)
        
        if self.parent:
            self.parent.update()

    def continue_after_feedback(self):
        """Продолжить после обратной связи"""
        if self.state == 'showing_feedback':
            self.state = 'running'
            self.show_feedback = False
            self.show_next_stimulus()

    def finish_test(self):
        """Завершить тест"""
        print("=" * 50)
        print("ТЕСТ СТРУПА ЗАВЕРШЕН")
        
        total_time = time.time() - self.start_time
        
        if self.reaction_times:
            avg_rt = sum(self.reaction_times) / len(self.reaction_times)
        else:
            avg_rt = 0
        
        accuracy = (self.correct_count / self.total_trials) * 100
        
        # Разделяем на конгруэнтные и неконгруэнтные
        congruent_times = []
        incongruent_times = []
        
        for i, trial in enumerate(self.trials):
            if i < len(self.reaction_times):
                if trial['congruent']:
                    congruent_times.append(self.reaction_times[i])
                else:
                    incongruent_times.append(self.reaction_times[i])
        
        avg_congruent = sum(congruent_times)/len(congruent_times) if congruent_times else 0
        avg_incongruent = sum(incongruent_times)/len(incongruent_times) if incongruent_times else 0
        stroop_effect = avg_incongruent - avg_congruent
        
        print(f"Общее время: {total_time:.2f} с")
        print(f"Точность: {accuracy:.1f}% ({self.correct_count}/{self.total_trials})")
        print(f"Ср. время реакции: {avg_rt:.3f} с")
        print(f"Конгруэнтные: {avg_congruent:.3f} с ({len(congruent_times)} попыток)")
        print(f"Неконгруэнтные: {avg_incongruent:.3f} с ({len(incongruent_times)} попыток)")
        print(f"Эффект Струпа: {stroop_effect:.3f} с")
        print("=" * 50)
        
        result = {
            'test_name': 'Тест Струпа',
            'total_rt': total_time,
            'avg_reaction_time': avg_rt,
            'accuracy': accuracy,
            'correct_count': self.correct_count,
            'total_trials': self.total_trials,
            'avg_congruent': avg_congruent,
            'avg_incongruent': avg_incongruent,
            'stroop_effect': stroop_effect,
            'reaction_times': self.reaction_times
        }
        
        self.finished.emit(result)
        self.state = 'finished'

    def stop_timers(self):
        if self.timer.isActive():
            self.timer.stop()