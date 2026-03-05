# tests/working_memory.py
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
import random
import time
from config import COLORS

class WorkingMemoryTest(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.state = 'waiting_start'
        self.grid_size = 5
        self.cell_size = 70  # Немного уменьшим для большего пространства
        self.grid = []
        self.target_color = None
        self.target_parity = None
        self.phase = 'color'
        self.start_time = None
        self.correct_color_count = 0
        self.correct_parity_count = 0
        self.error_color_count = 0
        self.error_parity_count = 0
        self.total_color_cells = 0
        self.total_parity_cells = 0
        self.display_time = 5000
        self.memorized_grid = []
        self.attempts = 0
        self.completed_count = 0
        self.total_targets = 0

    def get_button_rect(self):
        if not self.parent:
            return QRectF(0, 0, 160, 50)
        w, h = self.parent.width(), self.parent.height()
        return QRectF(w/2 - 80, h - 70, 160, 50)

    def init_grid(self):
        """Initialize 5x5 grid with random numbers 1-50 and colors"""
        self.grid = []
        numbers = random.sample(range(1, 51), self.grid_size * self.grid_size)
        
        colors = [
            QColor(255, 100, 100),    # Красный
            QColor(100, 255, 100),    # Зеленый
            QColor(100, 100, 255),    # Синий
        ]
        
        for i in range(self.grid_size):
            row = []
            for j in range(self.grid_size):
                number = numbers[i * self.grid_size + j]
                color = random.choice(colors)
                row.append({
                    'number': number,
                    'color': color,
                    'correct_color': False,
                    'correct_parity': False,
                    'selected': False,
                    'number_shown': True
                })
            self.grid.append(row)
        
        self.target_color = random.choice(colors)
        self.target_parity = random.choice(['even', 'odd'])
        
        self.total_color_cells = 0
        self.total_parity_cells = 0
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                cell = self.grid[i][j]
                if cell['color'] == self.target_color:
                    self.total_color_cells += 1
                    cell['correct_color'] = True
                if (self.target_parity == 'even' and cell['number'] % 2 == 0) or \
                   (self.target_parity == 'odd' and cell['number'] % 2 == 1):
                    self.total_parity_cells += 1
                    cell['correct_parity'] = True
        
        self.total_targets = self.total_color_cells + self.total_parity_cells
        self.completed_count = 0
        
        self.memorized_grid = []
        for row in self.grid:
            memorized_row = []
            for cell in row:
                memorized_row.append({
                    'number': cell['number'],
                    'color': cell['color'],
                    'correct_color': cell['correct_color'],
                    'correct_parity': cell['correct_parity']
                })
            self.memorized_grid.append(memorized_row)

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
            
            if text_width > rect.width() - 10:  # 5px padding с каждой стороны
                if len(current_line) > 1:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
                else:
                    lines.append(' '.join(current_line))
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Рисуем каждую строку
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
        # Преобразуем координаты в целые числа
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
                           "Оперативная память")
            
            font.setPointSize(14)
            painter.setFont(font)
            
            # Многострочное описание
            lines = [
                "Запомните числа и их цвета в течение 5 секунд,",
                "затем выберите сначала все клетки заданного цвета,",
                "а потом все клетки с чётными/нечётными числами."
            ]
            
            for i, line in enumerate(lines):
                painter.drawText(QRectF(0, 160 + i*30, w, 30), 
                               Qt.AlignmentFlag.AlignHCenter, line)
            
            if self.state != 'finished':
                self.draw_start_button(painter, pressed=False, label="СТАРТ")
            
        elif self.state == 'memorizing':
            # ТАБЛИЦА В ЦЕНТРЕ
            table_width = self.grid_size * self.cell_size
            table_height = self.grid_size * self.cell_size
            
            # Центральная позиция таблицы
            start_x = w/2 - table_width/2
            start_y = h/2 - table_height/2
            
            # 1. ЛЕВАЯ ПАНЕЛЬ - информация о запоминании
            left_panel_x = 20
            left_panel_y = start_y
            left_panel_width = 300  # Шире для текста
            left_panel_height = 200
            
            # Рисуем стилизованную панель
            content_rect = self.draw_panel(painter, left_panel_x, left_panel_y, 
                                         left_panel_width, left_panel_height, 
                                         "ЗАПОМИНАНИЕ", QColor(60, 100, 150))
            
            painter.setPen(QColor(50, 50, 50))
            
            # Таймер и инструкция
            if self.start_time:
                elapsed = time.time() - self.start_time
                remaining = self.display_time / 1000 - elapsed
                
                if remaining > 0:
                    font.setPointSize(12)
                    font.setBold(True)
                    painter.setFont(font)
                    
                    # Основная инструкция
                    instruction = "Запомните числа и их цвета в таблице"
                    instruction_rect = QRectF(content_rect.x(), content_rect.y(), 
                                            content_rect.width(), 50)
                    self.draw_wrapped_text(painter, instruction_rect, instruction, 12, Qt.AlignmentFlag.AlignCenter)
                    
                    font.setBold(False)
                    painter.setFont(font)
                    
                    # Таймер
                    timer_rect = QRectF(content_rect.x(), content_rect.y() + 60, 
                                      content_rect.width(), 40)
                    painter.setPen(QColor(200, 50, 50))
                    font.setPointSize(14)
                    font.setBold(True)
                    painter.setFont(font)
                    
                    timer_text = f"Осталось: {remaining:.1f} сек"
                    painter.drawText(timer_rect, Qt.AlignmentFlag.AlignCenter, timer_text)
                    
                    painter.setPen(QColor(50, 50, 50))
                    font.setPointSize(11)
                    font.setBold(False)
                    painter.setFont(font)
                    
                    # Дополнительная информация
                    info_text = "После 5 секунд таблица скроется"
                    info_rect = QRectF(content_rect.x(), content_rect.y() + 110, 
                                     content_rect.width(), 30)
                    self.draw_wrapped_text(painter, info_rect, info_text, 11, Qt.AlignmentFlag.AlignCenter)
            
            # 2. ПРАВАЯ ПАНЕЛЬ - информация о целях
            right_panel_x = w - left_panel_width - 20
            right_panel_y = start_y
            right_panel_width = left_panel_width
            right_panel_height = left_panel_height
            
            # Рисуем стилизованную панель
            content_rect = self.draw_panel(painter, right_panel_x, right_panel_y,
                                         right_panel_width, right_panel_height,
                                         "ЦЕЛИ", QColor(150, 80, 50))
            
            painter.setPen(QColor(50, 50, 50))
            font.setPointSize(12)
            painter.setFont(font)
            
            # Цвет цели
            color_name = self.get_color_name(self.target_color)
            color_rect = QRectF(content_rect.x(), content_rect.y() + 10, 
                              content_rect.width(), 40)
            
            painter.setPen(QColor(80, 80, 200))
            font.setBold(True)
            painter.setFont(font)
            
            color_text = f"Запомните {color_name} клетки"
            self.draw_wrapped_text(painter, color_rect, color_text, 12, Qt.AlignmentFlag.AlignCenter)
            
            # Цветной индикатор
            color_indicator_rect = QRectF(content_rect.center().x() - 40, 
                                        color_rect.bottom() + 5, 80, 20)
            painter.setBrush(QBrush(self.target_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(color_indicator_rect, 5, 5)
            
            # Четность цели
            parity_name = "чётные" if self.target_parity == 'even' else "нечётные"
            parity_rect = QRectF(content_rect.x(), color_indicator_rect.bottom() + 15, 
                               content_rect.width(), 40)
            
            painter.setPen(QColor(80, 150, 80))
            font.setBold(True)
            painter.setFont(font)
            
            parity_text = f"Запомните {parity_name} числа"
            self.draw_wrapped_text(painter, parity_rect, parity_text, 12, Qt.AlignmentFlag.AlignCenter)
            
            # Информация о задачах
            painter.setPen(QColor(100, 100, 100))
            font.setPointSize(11)
            font.setBold(False)
            painter.setFont(font)
            
            tasks_text = "Это понадобится в следующей фазе"
            tasks_rect = QRectF(content_rect.x(), parity_rect.bottom() + 20,
                              content_rect.width(), 30)
            self.draw_wrapped_text(painter, tasks_rect, tasks_text, 11, Qt.AlignmentFlag.AlignCenter)
            
            # 3. ТАБЛИЦА ПО ЦЕНТРУ
            self.draw_table(painter, start_x, start_y, show_numbers=True)
            
        elif self.state == 'testing':
            # ТАБЛИЦА В ЦЕНТРЕ
            table_width = self.grid_size * self.cell_size
            table_height = self.grid_size * self.cell_size
            
            # Центральная позиция таблицы
            start_x = w/2 - table_width/2
            start_y = h/2 - table_height/2
            
            # 1. ЛЕВАЯ ПАНЕЛЬ - статистика и информация
            left_panel_x = 20
            left_panel_y = start_y
            left_panel_width = 300
            left_panel_height = 220
            
            # Определяем фазу для заголовка
            if self.phase == 'color':
                phase_title = "ФАЗА 1: ЦВЕТ"
                title_color = QColor(80, 100, 180)
            else:
                phase_title = "ФАЗА 2: ЧЕТНОСТЬ"
                title_color = QColor(100, 150, 80)
            
            # Рисуем стилизованную панель
            content_rect = self.draw_panel(painter, left_panel_x, left_panel_y,
                                         left_panel_width, left_panel_height,
                                         phase_title, title_color)
            
            painter.setPen(QColor(50, 50, 50))
            
            # Информация о текущей фазе
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            
            if self.phase == 'color':
                color_name = self.get_color_name(self.target_color)
                instruction = f"Найдите {color_name} клетки"
            else:
                parity_name = "чётные" if self.target_parity == 'even' else "нечётные"
                instruction = f"Найдите {parity_name} числа"
            
            # Инструкция
            instruction_rect = QRectF(content_rect.x(), content_rect.y(),
                                    content_rect.width(), 50)
            self.draw_wrapped_text(painter, instruction_rect, instruction, 12, Qt.AlignmentFlag.AlignCenter)
            
            # Индикатор попытки
            font.setPointSize(11)
            font.setBold(True)
            painter.setFont(font)
            
            painter.setPen(QColor(150, 100, 50))
            attempt_rect = QRectF(content_rect.x(), content_rect.y() + 60,
                                content_rect.width(), 30)
            painter.drawText(attempt_rect, Qt.AlignmentFlag.AlignCenter,
                           f"Попытка: {self.attempts}/3")
            
            # Данные статистики
            correct_selected = self.get_correct_selected_count()
            
            if self.phase == 'color':
                total_needed = self.total_color_cells
                errors = self.error_color_count
            else:
                total_needed = self.total_parity_cells
                errors = self.error_parity_count
            
            # Прогресс
            font.setPointSize(13)
            font.setBold(True)
            painter.setFont(font)
            
            progress_rect = QRectF(content_rect.x(), content_rect.y() + 100,
                                 content_rect.width(), 40)
            
            if total_needed > 0:
                progress = (correct_selected / total_needed) * 100
                painter.setPen(QColor(70, 130, 180))
                progress_text = f"Найдено: {correct_selected}/{total_needed}"
            else:
                painter.setPen(QColor(150, 150, 150))
                progress_text = "Найдено: -/-"
            
            self.draw_wrapped_text(painter, progress_rect, progress_text, 13, Qt.AlignmentFlag.AlignCenter)
            
            # Процент
            if total_needed > 0 and correct_selected > 0:
                percent_rect = QRectF(content_rect.x(), content_rect.y() + 140,
                                    content_rect.width(), 30)
                painter.setPen(QColor(100, 100, 150))
                font.setPointSize(12)
                painter.setFont(font)
                percent_text = f"({progress:.0f}%)"
                painter.drawText(percent_rect, Qt.AlignmentFlag.AlignCenter, percent_text)
            
            # Ошибки
            font.setPointSize(12)
            painter.setFont(font)
            
            errors_rect = QRectF(content_rect.x(), content_rect.y() + 170,
                               content_rect.width(), 30)
            
            if errors == 0:
                painter.setPen(QColor(80, 180, 80))
                errors_text = "✓ Нет ошибок"
            else:
                painter.setPen(QColor(220, 80, 80))
                errors_text = f"✗ Ошибок: {errors}"
            
            painter.drawText(errors_rect, Qt.AlignmentFlag.AlignCenter, errors_text)
            
            # 2. ПРАВАЯ ПАНЕЛЬ - кнопки действий
            right_panel_x = w - left_panel_width - 20
            right_panel_y = start_y
            right_panel_width = left_panel_width
            right_panel_height = left_panel_height
            
            # Рисуем стилизованную панель
            content_rect = self.draw_panel(painter, right_panel_x, right_panel_y,
                                         right_panel_width, right_panel_height,
                                         "УПРАВЛЕНИЕ", QColor(130, 80, 150))
            
            painter.setPen(QColor(50, 50, 50))
            font.setPointSize(12)
            painter.setFont(font)
            
            # Инструкция по выбору
            instruction_text = "Кликните на клетку таблицы"
            instruction_rect = QRectF(content_rect.x(), content_rect.y(),
                                    content_rect.width(), 40)
            self.draw_wrapped_text(painter, instruction_rect, instruction_text, 12, Qt.AlignmentFlag.AlignCenter)
            
            # Информация о цветах
            info_text = "Зеленый - правильно"
            info_rect = QRectF(content_rect.x(), content_rect.y() + 45,
                             content_rect.width(), 40)
            painter.setPen(QColor(80, 150, 80))
            self.draw_wrapped_text(painter, info_rect, info_text, 11, Qt.AlignmentFlag.AlignCenter)
            
            info_text2 = "Красный - ошибка"
            info_rect2 = QRectF(content_rect.x(), content_rect.y() + 70,
                              content_rect.width(), 40)
            painter.setPen(QColor(220, 80, 80))
            self.draw_wrapped_text(painter, info_rect2, info_text2, 11, Qt.AlignmentFlag.AlignCenter)
            
            # Кнопка ДАЛЕЕ или ЗАВЕРШИТЬ
            if correct_selected >= total_needed and total_needed > 0:
                btn_y = content_rect.y() + 120
                btn_height = 40
                
                if self.phase == 'color':
                    btn_label = "ДАЛЕЕ"
                    btn_color = QColor(70, 130, 200)
                else:
                    btn_label = "ЗАВЕРШИТЬ"
                    btn_color = QColor(180, 70, 70)
                
                # Рисуем стилизованную кнопку
                btn_rect = QRectF(content_rect.x() + 50, btn_y, 
                                content_rect.width() - 100, btn_height)
                
                # Тень кнопки
                painter.setBrush(QBrush(btn_color.darker(140)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(btn_rect.translated(0, 2), 6, 6)
                
                # Основная кнопка
                painter.setBrush(QBrush(btn_color))
                painter.setPen(QPen(btn_color.lighter(150), 1))
                painter.drawRoundedRect(btn_rect, 6, 6)
                
                # Текст кнопки
                painter.setPen(QColor(255, 255, 255))
                font.setPointSize(13)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, btn_label)
                
                # Подсказка
                font.setPointSize(10)
                font.setBold(False)
                painter.setFont(font)
                painter.setPen(QColor(100, 100, 100))
                
                if self.phase == 'color':
                    hint_text = "перейти к фазе 2"
                else:
                    hint_text = "завершить тест"
                
                hint_rect = QRectF(content_rect.x(), btn_rect.bottom() + 5,
                                 content_rect.width(), 20)
                painter.drawText(hint_rect, Qt.AlignmentFlag.AlignCenter, hint_text)
            else:
                # Сообщение о необходимости завершить выбор
                font.setPointSize(12)
                font.setBold(True)
                painter.setFont(font)
                
                painter.setPen(QColor(150, 120, 80))
                message_rect = QRectF(content_rect.x(), content_rect.y() + 120,
                                    content_rect.width(), 60)
                
                if total_needed > 0:
                    remaining = total_needed - correct_selected
                    if remaining > 0:
                        message_text = f"Найдите ещё {remaining}"
                    else:
                        message_text = "Найдите все цели"
                else:
                    message_text = "Найдите цели"
                
                self.draw_wrapped_text(painter, message_rect, message_text, 12, Qt.AlignmentFlag.AlignCenter)
            
            # 3. ТАБЛИЦА ПО ЦЕНТРУ (между панелями)
            self.draw_table(painter, start_x, start_y, show_numbers=False)

    def draw_table(self, painter, start_x, start_y, show_numbers=True):
        """Отрисовка таблицы в указанной позиции"""
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                cell = self.grid[i][j]
                x = start_x + j * self.cell_size
                y = start_y + i * self.cell_size
                
                # Цвет ячейки
                if self.state == 'memorizing':
                    painter.setBrush(QBrush(cell['color']))
                elif self.state == 'testing':
                    if cell.get('selected', False):
                        if self.phase == 'color':
                            is_correct = self.memorized_grid[i][j]['correct_color']
                        else:
                            is_correct = self.memorized_grid[i][j]['correct_parity']
                        
                        if is_correct:
                            painter.setBrush(QBrush(QColor(100, 255, 100)))  # Зеленый
                        else:
                            painter.setBrush(QBrush(QColor(255, 100, 100)))  # Красный
                    else:
                        painter.setBrush(QBrush(QColor(240, 240, 240)))  # Серый
                
                painter.setPen(QPen(QColor(150, 150, 150), 1))
                painter.drawRect(QRectF(x, y, self.cell_size, self.cell_size))
                
                # Число (только если нужно показывать)
                if show_numbers:
                    painter.setPen(COLORS['text'])
                    font = painter.font()
                    font.setPointSize(16)
                    font.setBold(True)
                    painter.setFont(font)
                    painter.drawText(QRectF(x, y, self.cell_size, self.cell_size),
                                   Qt.AlignmentFlag.AlignCenter, str(cell['number']))

    def get_color_name(self, color):
        if color == QColor(255, 100, 100):
            return "красные"
        elif color == QColor(100, 255, 100):
            return "зелёные"
        elif color == QColor(100, 100, 255):
            return "синие"
        return ""

    def get_correct_selected_count(self):
        """Подсчитать количество правильно выбранных клеток"""
        count = 0
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j].get('selected', False):
                    if self.phase == 'color':
                        if self.memorized_grid[i][j]['correct_color']:
                            count += 1
                    else:
                        if self.memorized_grid[i][j]['correct_parity']:
                            count += 1
        return count

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
        
        elif self.state == 'testing':
            w, h = self.parent.width(), self.parent.height()
            
            # Определяем позицию таблицы
            table_width = self.grid_size * self.cell_size
            table_height = self.grid_size * self.cell_size
            start_x = w/2 - table_width/2
            start_y = h/2 - table_height/2
            
            # Проверяем клик по таблице
            click_x, click_y = event.position().x(), event.position().y()
            
            if (start_x <= click_x <= start_x + table_width and
                start_y <= click_y <= start_y + table_height):
                
                col = int((click_x - start_x) // self.cell_size)
                row = int((click_y - start_y) // self.cell_size)
                
                if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                    if not self.grid[row][col].get('selected', False):
                        self.grid[row][col]['selected'] = True
                        
                        if self.phase == 'color':
                            if not self.memorized_grid[row][col]['correct_color']:
                                self.error_color_count += 1
                        else:
                            if not self.memorized_grid[row][col]['correct_parity']:
                                self.error_parity_count += 1
                    
                    self.parent.update()
                return
            
            # Проверяем клик по кнопке в правой панели
            correct_selected = self.get_correct_selected_count()
            
            if self.phase == 'color':
                total_needed = self.total_color_cells
            else:
                total_needed = self.total_parity_cells
            
            if correct_selected >= total_needed and total_needed > 0:
                # Координаты правой панели
                right_panel_x = w - 320  # 300 + 20
                right_panel_y = start_y
                right_panel_width = 300
                
                # Координаты кнопки
                content_rect = QRectF(right_panel_x + 10, right_panel_y + 40, 
                                    right_panel_width - 20, 220 - 45)
                
                btn_y = content_rect.y() + 120
                btn_height = 40
                btn_rect = QRectF(content_rect.x() + 50, btn_y, 
                                content_rect.width() - 100, btn_height)
                
                if btn_rect.contains(event.position()):
                    if self.phase == 'color':
                        self.complete_color_phase()
                    else:
                        self.complete_parity_phase()

    def start_test(self):
        self.attempts += 1
        self.state = 'memorizing'
        self.init_grid()
        self.correct_color_count = 0
        self.correct_parity_count = 0
        self.error_color_count = 0
        self.error_parity_count = 0
        self.phase = 'color'
        self.start_time = time.time()
        
        QTimer.singleShot(self.display_time, self.start_testing_phase)
        
        if self.parent:
            self.parent.update()

    def start_testing_phase(self):
        self.state = 'testing'
        
        for row in self.grid:
            for cell in row:
                cell['selected'] = False
                cell['number_shown'] = False
        
        if self.parent:
            self.parent.update()

    def complete_color_phase(self):
        self.correct_color_count = self.get_correct_selected_count()
        self.phase = 'parity'
        
        for row in self.grid:
            for cell in row:
                cell['selected'] = False
        
        self.error_parity_count = 0
        
        if self.parent:
            self.parent.update()

    def complete_parity_phase(self):
        self.correct_parity_count = self.get_correct_selected_count()
        self.finish_test()

    def finish_test(self):
        color_accuracy = (self.correct_color_count / self.total_color_cells * 100) if self.total_color_cells > 0 else 0
        parity_accuracy = (self.correct_parity_count / self.total_parity_cells * 100) if self.total_parity_cells > 0 else 0
        
        total_correct = self.correct_color_count + self.correct_parity_count
        total_errors = self.error_color_count + self.error_parity_count
        total_targets = self.total_color_cells + self.total_parity_cells
        
        selection_score = (total_correct / total_targets * 50) if total_targets > 0 else 0
        error_penalty = min(50, total_errors * 10)
        error_score = 50 - error_penalty
        overall_accuracy = selection_score + error_score
        
        result = {
            'test_name': 'Оперативная память',
            'latency': 0,
            'motor_time': 0,
            'total_rt': time.time() - self.start_time if self.start_time else 0,
            'correct': overall_accuracy > 70,
            'correct_count': total_correct,
            'total_trials': total_targets,
            'accuracy': overall_accuracy,
            'target_color': self.get_color_name(self.target_color),
            'target_parity': 'чётные' if self.target_parity == 'even' else 'нечётные',
            'color_correct': self.correct_color_count,
            'color_total': self.total_color_cells,
            'color_accuracy': color_accuracy,
            'color_errors': self.error_color_count,
            'parity_correct': self.correct_parity_count,
            'parity_total': self.total_parity_cells,
            'parity_accuracy': parity_accuracy,
            'parity_errors': self.error_parity_count,
            'total_errors': total_errors,
            'memory_load': self.grid_size * self.grid_size,
            'attempts': self.attempts
        }
        
        self.finished.emit(result)
        self.state = 'finished'
        
        if self.parent:
            self.parent.update()

    def stop_timers(self):
        pass