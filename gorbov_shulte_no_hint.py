# tests/gorbov_shulte_no_hint.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import time
import random
from config import COLORS

class GorbovShulteTestNoHint(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.start_time = None
        self.grid_size = 7
        self.numbers = []
        self.colors = []
        self.click_time = None
        self.reaction_times = []
        self.errors = 0
        self.cell_size = 60
        self.completed_count = 0
        self.total_targets = 49
        
        self.red_sequence = list(range(1, 26))
        self.black_sequence = list(range(24, 0, -1))
        self.current_red_index = 0
        self.current_black_index = 0
        self.is_red_turn = True
        
        self.last_found_number = None
        self.last_found_color = None

    def get_button_rect(self):
        if not self.parent:
            return QRectF(0, 0, 160, 50)
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 70, 160, 50)

    def draw_wrapped_text(self, painter, rect, text, font_size=12, alignment=Qt.AlignmentFlag.AlignLeft, line_spacing=3):
        """Рисует текст с переносом строк"""
        font = painter.font()
        font.setPointSize(font_size)
        painter.setFont(font)
        
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            text_width = painter.fontMetrics().boundingRect(test_line).width()
            
            if text_width > rect.width() - 10:
                if len(current_line) > 1:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
                else:
                    lines.append(' '.join(current_line))
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        line_height = painter.fontMetrics().height()
        y = rect.top()
        
        for i, line in enumerate(lines):
            if y + line_height > rect.bottom():
                break
            painter.drawText(QRectF(rect.left() + 5, y, rect.width() - 10, line_height),
                           alignment, line)
            y += line_height + line_spacing
        
        return len(lines)

    def draw_panel(self, painter, x, y, width, height, title, title_color=QColor(70, 70, 70)):
        """Рисует стилизованную панель с тенью и заголовком"""
        x_int, y_int = int(x), int(y)
        width_int, height_int = int(width), int(height)
        
        # Тень панели
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(x_int + 2, y_int + 2, width_int, height_int), 8, 8)
        
        # Основная панель
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(QRectF(x_int, y_int, width_int, height_int), 8, 8)
        
        # Заголовок панели
        painter.setPen(title_color)
        font = painter.font()
        font.setPointSize(13)
        font.setBold(True)
        painter.setFont(font)
        
        # Фон заголовка
        painter.setBrush(QBrush(QColor(245, 245, 245)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(x_int, y_int, width_int, 35), 8, 8)
        
        # Обводка заголовка
        painter.setPen(QPen(QColor(220, 220, 220), 1))
        painter.drawLine(x_int, y_int + 35, x_int + width_int, y_int + 35)
        
        # Текст заголовка
        painter.setPen(title_color)
        title_rect = QRectF(x_int + 10, y_int + 5, width_int - 20, 25)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title)
        
        return QRectF(x_int + 10, y_int + 40, width_int - 20, height_int - 45)

    def paint(self, painter):
        if not self.parent:
            return
            
        w, h = self.parent.width(), self.parent.height()
        painter.fillRect(self.parent.rect(), COLORS['bg'])
        painter.setPen(COLORS['text'])
        font = painter.font()
        font.setFamily("DejaVu Sans")

        if self.state == 'waiting_start':
            # Экран старта
            font.setPointSize(20)
            painter.setFont(font)
            painter.drawText(QRectF(0, 100, w, 50), Qt.AlignmentFlag.AlignHCenter,
                           "Таблицы Горбова-Шульте (строгий режим)")
            
            font.setPointSize(14)
            painter.setFont(font)
            
            # Многострочное описание
            lines = [
                "Найдите числа в последовательности:",
                "КРАСНАЯ 1 → ЧЕРНАЯ 24 → КРАСНАЯ 2 → ЧЕРНАЯ 23 → ...",
                "Красные числа: 1-25, Черные числа: 24-1 (без 25)",
                "БЕЗ ПОДСКАЗОК - запоминайте последовательность самостоятельно"
            ]
            
            for i, line in enumerate(lines):
                painter.drawText(QRectF(0, 160 + i*30, w, 30), 
                               Qt.AlignmentFlag.AlignHCenter, line)
            
            if self.state != 'finished':
                self.draw_start_button(painter, pressed=False, label="СТАРТ")
            
        elif self.state == 'running':
            # ТАБЛИЦА В ЦЕНТРЕ
            table_width = self.grid_size * self.cell_size
            table_height = self.grid_size * self.cell_size
            
            # Центральная позиция таблицы
            start_x = w/2 - table_width/2
            start_y = h/2 - table_height/2
            
            # Уменьшенная ширина панелей
            panel_width = 250
            
            # 1. ЛЕВАЯ ПАНЕЛЬ - информация о цели и статистика
            left_panel_x = 20
            left_panel_y = start_y
            panel_height = 180
            
            # Рисуем стилизованную панель
            content_rect = self.draw_panel(painter, left_panel_x, left_panel_y,
                                         panel_width, panel_height,
                                         "ЦЕЛЬ И СТАТИСТИКА", QColor(180, 60, 60))
            
            painter.setPen(QColor(50, 50, 50))
            
            # Определяем цель
            if self.is_red_turn:
                target_color_name = "КРАСНЫЙ"
                target_number = self.red_sequence[self.current_red_index]
            else:
                target_color_name = "ЧЕРНЫЙ"
                target_number = self.black_sequence[self.current_black_index]
            
            # Текущая цель
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            
            target_text = f"Цель: {target_color_name} {target_number}"
            target_rect = QRectF(content_rect.x(), content_rect.y(),
                               content_rect.width(), 30)
            painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter, target_text)
            
            # Информация о строгом режиме
            font.setPointSize(11)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor(180, 60, 60))
            
            mode_rect = QRectF(content_rect.x(), content_rect.y() + 35,
                             content_rect.width(), 20)
            painter.drawText(mode_rect, Qt.AlignmentFlag.AlignCenter,
                           "СТРОГИЙ РЕЖИМ")
            
            # Статистика
            painter.setPen(QColor(50, 50, 50))
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            
            # Прогресс
            progress_rect = QRectF(content_rect.x(), content_rect.y() + 60,
                                 content_rect.width(), 25)
            painter.drawText(progress_rect, Qt.AlignmentFlag.AlignCenter,
                           f"Прогресс: {self.completed_count}/{self.total_targets}")
            
            # Последнее найденное
            if self.last_found_number:
                color_name = "КРАСНЫЙ" if self.last_found_color == 'red' else "ЧЕРНЫЙ"
                found_rect = QRectF(content_rect.x(), content_rect.y() + 90,
                                  content_rect.width(), 25)
                painter.drawText(found_rect, Qt.AlignmentFlag.AlignCenter,
                               f"Найдено: {color_name} {self.last_found_number}")
            
            # Время
            elapsed = time.time() - self.start_time if self.start_time else 0
            time_rect = QRectF(content_rect.x(), content_rect.y() + 120,
                             content_rect.width(), 25)
            painter.drawText(time_rect, Qt.AlignmentFlag.AlignCenter,
                           f"Время: {elapsed:.1f} с")
            
            # Ошибки
            painter.setPen(QColor(150, 50, 50) if self.errors > 0 else QColor(80, 150, 80))
            errors_rect = QRectF(content_rect.x(), content_rect.y() + 150,
                               content_rect.width(), 25)
            
            if self.errors == 0:
                errors_text = "✓ Нет ошибок"
            else:
                errors_text = f"✗ Ошибок: {self.errors}"
            
            painter.drawText(errors_rect, Qt.AlignmentFlag.AlignCenter, errors_text)
            
            # 2. ПРАВАЯ ПАНЕЛЬ - последовательность
            right_panel_x = w - panel_width - 20
            right_panel_y = start_y
            
            # Рисуем стилизованную панель
            content_rect = self.draw_panel(painter, right_panel_x, right_panel_y,
                                         panel_width, panel_height,
                                         "ПОСЛЕДОВАТЕЛЬНОСТЬ", QColor(80, 100, 180))
            
            painter.setPen(QColor(50, 50, 50))
            font.setPointSize(12)
            painter.setFont(font)
            
            # Инструкция
            instruction_text = "Запомните последовательность:"
            instruction_rect = QRectF(content_rect.x(), content_rect.y(),
                                    content_rect.width(), 30)
            painter.drawText(instruction_rect, Qt.AlignmentFlag.AlignCenter, instruction_text)
            
            # Последовательность
            font.setPointSize(10)
            painter.setFont(font)
            
            seq_rect = QRectF(content_rect.x(), content_rect.y() + 35,
                            content_rect.width(), 40)
            seq_text = "КРАСНАЯ 1 → ЧЕРНАЯ 24 → КРАСНАЯ 2 → ЧЕРНАЯ 23 → ..."
            self.draw_wrapped_text(painter, seq_rect, seq_text, 10, Qt.AlignmentFlag.AlignCenter)
            
            # Числа
            numbers_rect = QRectF(content_rect.x(), content_rect.y() + 80,
                                content_rect.width(), 35)
            numbers_text = "Красные: 1-25\nЧерные: 24-1 (без 25)"
            painter.setPen(QColor(80, 80, 80))
            painter.drawText(numbers_rect, Qt.AlignmentFlag.AlignCenter, numbers_text)
            
            # Формула для запоминания
            painter.setPen(QColor(100, 100, 100))
            font.setPointSize(9)
            painter.setFont(font)
            
            formula_rect = QRectF(content_rect.x(), content_rect.y() + 120,
                                content_rect.width(), 40)
            formula_text = "R1 → B24 → R2 → B23 → R3 → B22 ..."
            painter.drawText(formula_rect, Qt.AlignmentFlag.AlignCenter, formula_text)
            
            # 3. ТАБЛИЦА ПО ЦЕНТРУ (между панелями)
            # Проверяем перекрытие и корректируем
            if left_panel_x + panel_width > start_x:
                start_x = left_panel_x + panel_width + 20
            
            if right_panel_x < start_x + table_width:
                start_x = right_panel_x - table_width - 20
            
            self.draw_table(painter, start_x, start_y)

    def draw_table(self, painter, start_x, start_y):
        """Отрисовка таблицы без подсветки"""
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                idx = row * self.grid_size + col
                if idx < len(self.numbers):
                    x = start_x + col * self.cell_size
                    y = start_y + row * self.cell_size
                    
                    # Получаем данные ячейки
                    number = self.numbers[idx]
                    color_name = self.colors[idx]
                    
                    # Цвет числа
                    if color_name == 'red':
                        text_color = QColor(220, 80, 80)
                        bg_color = QColor(255, 240, 240)
                    else:
                        text_color = QColor(60, 60, 60)
                        bg_color = QColor(245, 245, 245)
                    
                    # Фон ячейки
                    painter.setBrush(QBrush(bg_color))
                    painter.setPen(QPen(QColor(150, 150, 150), 1))
                    painter.drawRect(QRectF(x, y, self.cell_size, self.cell_size))
                    
                    # Число
                    painter.setPen(text_color)
                    font = painter.font()
                    font.setPointSize(14)
                    font.setBold(True)
                    painter.setFont(font)
                    
                    painter.drawText(QRectF(x, y, self.cell_size, self.cell_size),
                                   Qt.AlignmentFlag.AlignCenter, str(number))

    def draw_start_button(self, painter, pressed=False, label="СТАРТ"):
        btn_rect = self.get_button_rect()
        color = COLORS['start_btn'].darker(120) if pressed else COLORS['start_btn']
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(btn_rect, 10, 10)
        
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(COLORS['text'])
        painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, label)

    def mousePressEvent(self, event):
        if self.state == 'waiting_start':
            btn_rect = self.get_button_rect()
            if btn_rect.contains(event.position()):
                self.start_test()
        
        elif self.state == 'running':
            w, h = self.parent.width(), self.parent.height()
            
            # Определяем позицию таблицы
            table_width = self.grid_size * self.cell_size
            table_height = self.grid_size * self.cell_size
            
            # Вычисляем start_x заново
            panel_width = 250
            left_panel_x = 20
            right_panel_x = w - panel_width - 20
            start_x = w/2 - table_width/2
            start_y = h/2 - table_height/2
            
            # Проверяем перекрытие и корректируем
            if left_panel_x + panel_width > start_x:
                start_x = left_panel_x + panel_width + 20
            if right_panel_x < start_x + table_width:
                start_x = right_panel_x - table_width - 20
            
            # Проверяем клик по таблице
            click_x, click_y = event.position().x(), event.position().y()
            
            if (start_x <= click_x <= start_x + table_width and
                start_y <= click_y <= start_y + table_height):
                
                col = int((click_x - start_x) // self.cell_size)
                row = int((click_y - start_y) // self.cell_size)
                
                if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                    idx = row * self.grid_size + col
                    
                    if idx < len(self.numbers):
                        clicked_number = self.numbers[idx]
                        clicked_color = self.colors[idx]
                        click_time = time.time()
                        
                        # Определяем ожидаемое число и цвет
                        if self.is_red_turn:
                            expected_number = self.red_sequence[self.current_red_index]
                            expected_color = 'red'
                        else:
                            expected_number = self.black_sequence[self.current_black_index]
                            expected_color = 'black'
                        
                        # Проверяем правильность
                        correct = (clicked_number == expected_number and 
                                  clicked_color == expected_color)
                        
                        if not correct:
                            self.errors += 1
                            if self.parent:
                                self.parent.update()
                            return
                        
                        # Правильный клик
                        reaction_time = click_time - (self.click_time if self.click_time else self.start_time)
                        self.reaction_times.append(reaction_time)
                        self.click_time = click_time
                        self.completed_count += 1
                        
                        # Сохраняем последнее найденное
                        self.last_found_number = clicked_number
                        self.last_found_color = clicked_color
                        
                        # Переходим к следующей цели
                        if self.is_red_turn:
                            self.current_red_index += 1
                            self.is_red_turn = False
                        else:
                            self.current_black_index += 1
                            self.is_red_turn = True
                        
                        # Проверяем завершение
                        if self.completed_count >= self.total_targets:
                            self.finish_test()
                        
                        if self.parent:
                            self.parent.update()

    def start_test(self):
        """Начать тест в строгом режиме"""
        self.state = 'running'
        self.start_time = time.time()
        self.current_red_index = 0
        self.current_black_index = 0
        self.is_red_turn = True
        self.completed_count = 0
        self.errors = 0
        self.reaction_times = []
        self.last_found_number = None
        self.last_found_color = None
        
        # Генерируем таблицу
        self.generate_table()
        
        if self.parent:
            self.parent.update()

    def generate_table(self):
        """Генерация таблицы с 25 красными (1-25) и 24 черными (24-1)"""
        numbers = []
        colors = []
        
        red_numbers = list(range(1, 26))
        random.shuffle(red_numbers)
        numbers.extend(red_numbers)
        colors.extend(['red'] * 25)
        
        black_numbers = list(range(24, 0, -1))
        random.shuffle(black_numbers)
        numbers.extend(black_numbers)
        colors.extend(['black'] * 24)
        
        paired = list(zip(numbers, colors))
        random.shuffle(paired)
        numbers, colors = zip(*paired)
        
        self.numbers = list(numbers)
        self.colors = list(colors)

    def finish_test(self):
        """Завершить тест"""
        total_time = time.time() - self.start_time
        
        if self.reaction_times:
            avg_rt = sum(self.reaction_times) / len(self.reaction_times)
        else:
            avg_rt = 0
        
        accuracy = ((self.total_targets - self.errors) / self.total_targets) * 100
        
        red_times = self.reaction_times[0::2]
        black_times = self.reaction_times[1::2]
        
        red_avg = sum(red_times) / len(red_times) if red_times else 0
        black_avg = sum(black_times) / len(black_times) if black_times else 0
        switch_cost = black_avg - red_avg
        
        result = {
            'test_name': 'Таблицы Горбова-Шульте (строгий)',
            'total_rt': total_time,
            'avg_reaction_time': avg_rt,
            'red_avg_rt': red_avg,
            'black_avg_rt': black_avg,
            'errors': self.errors,
            'accuracy': accuracy,
            'completed': True,
            'reaction_times': self.reaction_times,
            'switch_cost': switch_cost,
            'total_targets': self.total_targets,
            'found_targets': self.completed_count
        }
        
        self.finished.emit(result)
        self.state = 'finished'

    def stop_timers(self):
        pass