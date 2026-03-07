# main.py 
import sys
import os
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QMessageBox, QDialog, QTextEdit, 
    QDialogButtonBox, QFrame, QGridLayout, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QFont, QFontDatabase, QPalette, QIcon

from tests.simple_reaction import SimpleReactionTest
from tests.choice_reaction import ChoiceReactionTest
from tests.complex_choice import ComplexChoiceTest
from tests.combined_a import CombinedTestA
from tests.combined_b import CombinedTestB
from tests.tracking_following import TrackingFollowingTest
from tests.moving_object_reaction import MovingObjectReactionTest
from tests.attention_switching import AttentionSwitchingTest
from tests.trajectory_prediction import TrajectoryPredictionTest
from tests.gorbov_shulte import GorbovShulteTest
from tests.stroop_test import StroopTest
from tests.gorbov_shulte_no_hint import GorbovShulteTestNoHint
from tests.working_memory import WorkingMemoryTest
from tests.size_discrimination import SizeDiscriminationTest
from tests.color_discrimination import ColorDiscriminationTest
from report import generate_report, calculate_std
from cognitive_metrics import CognitiveMotorAnalyzer
from progress_tracker import ProgressTracker


class TestCard(QFrame):
    """Карточка теста - весь тест в одной рамке"""
    clicked = pyqtSignal()
    
    def __init__(self, title, description, category, color="#3498DB", parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #D5DBDB;
                border-radius: 4px;
                padding: 8px;
                margin: 4px;
            }}
            QFrame:hover {{
                background-color: #F8F9FA;
                border-color: #3498DB;
            }}
        """)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(95)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {color};
                padding: 0px;
                margin: 0px;
                background-color: transparent;
                border: none;
            }}
        """)
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #555555;
                padding: 0px;
                margin: 0px;
                background-color: transparent;
                border: none;
            }
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        cat_label = QLabel(category)
        cat_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #888888;
                font-style: italic;
                padding: 0px;
                margin: 0px;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(cat_label)
        
    def mousePressEvent(self, event):
        self.clicked.emit()


class TestRunner(QWidget):
    """Виджет для запуска теста"""
    
    def __init__(self, test_class, test_name, attempts, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.test_class = test_class
        self.test_name = test_name
        self.attempts = attempts
        self.current_attempt = 0
        self.results = []
        self.test = None
        self.is_active = True  # Флаг активности
        
        self.init_test()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def init_test(self):
        """Инициализировать тест"""
        if self.test is not None:
            try:
                if hasattr(self.test, 'stop_timers'):
                    self.test.stop_timers()
                if hasattr(self.test, 'finished'):
                    self.test.finished.disconnect()
                self.test.deleteLater()
            except:
                pass
        
        self.test = self.test_class(self)
        if hasattr(self.test, 'finished'):
            self.test.finished.connect(self.on_test_finished)
    
    def start_next_attempt(self):
        """Запустить следующую попытку"""
        if self.current_attempt >= self.attempts or not self.is_active:
            return
        
        if hasattr(self.parent(), 'update_attempt_display'):
            self.parent().update_attempt_display(self.current_attempt + 1, self.attempts)
        
        # Обновляем отображение
        self.update()
    
    def on_test_finished(self, result):
        """Обработчик завершения попытки"""
        if not self.is_active:
            return
            
        if isinstance(result, dict):
            result['attempt_number'] = self.current_attempt + 1
            self.results.append(result)
        
        self.current_attempt += 1
        
        if self.current_attempt < self.attempts:
            # Задержка перед следующей попыткой
            QTimer.singleShot(1000, self.restart_test)
        else:
            avg_result = self.calculate_average_result()
            avg_result['test_name'] = self.test_name
            self.main_window.on_test_complete(avg_result)
    
    def restart_test(self):
        """Перезапустить тест для следующей попытки"""
        if not self.is_active:
            return
            
        self.init_test()
        self.update()
        self.start_next_attempt()
    
    def calculate_average_result(self):
        """Рассчитать средний результат по попыткам"""
        if not self.results:
            return {}
        
        result_data = {
            'test_name': self.test_name,
            'attempts': self.attempts,
            'attempt_results': self.results,
            'total_correct': sum(1 for r in self.results if isinstance(r, dict) and r.get('correct', False)),
            'total_attempts': len(self.results)
        }
        
        numeric_metrics = {}
        all_numeric_keys = set()
        
        for result in self.results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        all_numeric_keys.add(key)
        
        for key in all_numeric_keys:
            values = []
            for result in self.results:
                if isinstance(result, dict):
                    value = result.get(key)
                    if isinstance(value, (int, float)):
                        values.append(value)
            
            if values:
                numeric_metrics[f'avg_{key}'] = sum(values) / len(values)
                numeric_metrics[f'min_{key}'] = min(values)
                numeric_metrics[f'max_{key}'] = max(values)
                if len(values) > 1:
                    numeric_metrics[f'std_{key}'] = calculate_std(values)
        
        result_data.update(numeric_metrics)
        
        return result_data

    def paintEvent(self, event):
        if self.test and hasattr(self.test, 'paint'):
            try:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.test.paint(painter)
            except RuntimeError:
                pass

    def mousePressEvent(self, event):
        if self.test and hasattr(self.test, 'mousePressEvent'):
            try:
                self.test.mousePressEvent(event)
            except RuntimeError:
                pass

    def mouseReleaseEvent(self, event):
        if self.test and hasattr(self.test, 'mouseReleaseEvent'):
            try:
                self.test.mouseReleaseEvent(event)
            except RuntimeError:
                pass

    def mouseMoveEvent(self, event):
        if self.test and hasattr(self.test, 'mouseMoveEvent'):
            try:
                self.test.mouseMoveEvent(event)
            except RuntimeError:
                pass

    def stop_all_timers(self):
        """Остановить все таймеры теста"""
        self.is_active = False
        if self.test and hasattr(self.test, 'stop_timers'):
            try:
                self.test.stop_timers()
            except:
                pass
    
    def closeEvent(self, event):
        """Обработчик закрытия виджета"""
        self.stop_all_timers()
        event.accept()


class InstructionsDialog(QDialog):
    """Диалог с инструкциями"""
    
    def __init__(self, test_name, instructions, attempts, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Инструкция: {test_name}")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(test_name)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2C3E50;
                padding: 10px;
                border-bottom: 2px solid #3498DB;
            }
        """)
        layout.addWidget(title_label)
        
        attempts_label = QLabel(f"Будет выполнено попыток: {attempts}")
        attempts_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #3498DB;
                padding: 5px;
            }
        """)
        layout.addWidget(attempts_label)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #D5DBDB;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        text_edit.setText(instructions)
        layout.addWidget(text_edit, 1)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Начать")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        
        layout.addWidget(button_box)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Когнитивные тесты")
        self.resize(1400, 800)
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(50, 50, 50))
        self.setPalette(palette)
        
        font_id = QFontDatabase.addApplicationFont("resources/DejaVuSans.ttf")
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"
        
        self.all_results = []
        self.attempts = 3
        self.analyzer = CognitiveMotorAnalyzer()
        self.progress_tracker = ProgressTracker()
        
        self.init_ui()
        self.init_test_list()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabBar::tab {
                background: #F0F0F0;
                color: #666666;
                padding: 8px 20px;
                margin-right: 2px;
                border: none;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #3498DB;
                border-bottom: 2px solid #3498DB;
            }
            QTabBar::tab:hover:!selected {
                background: #F8F8F8;
            }
        """)
        
        categories = ['Все', 'Базовые', 'Пространственные', 'Когнитивные', 'Перцептивные', 'Память', 'Комбинированные']
        self.test_tabs = {}
        
        for category in categories:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background: transparent;
                }
            """)
            
            container = QWidget()
            grid_layout = QGridLayout(container)
            grid_layout.setSpacing(12)
            grid_layout.setContentsMargins(8, 8, 8, 8)
            
            scroll.setWidget(container)
            tab_layout.addWidget(scroll)
            
            self.test_tabs[category] = (tab, grid_layout, container)
            self.tab_widget.addTab(tab, category)
        
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget, 1)
        
        control_panel = QFrame()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #DDDDDD;
                padding: 10px;
            }
        """)
        
        control_layout = QHBoxLayout(control_panel)
        
        self.stats_label = QLabel("Готов к тестированию")
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
            }
        """)
        control_layout.addWidget(self.stats_label)
        
        control_layout.addStretch()
        
        settings_label = QLabel("Попыток:")
        settings_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                margin-right: 5px;
            }
        """)
        control_layout.addWidget(settings_label)
        
        self.attempt_spin = QSpinBox()
        self.attempt_spin.setRange(1, 10)
        self.attempt_spin.setValue(self.attempts)
        self.attempt_spin.setFixedWidth(60)
        self.attempt_spin.setStyleSheet("""
            QSpinBox {
                padding: 3px;
                font-size: 12px;
                border: 1px solid #DDDDDD;
                border-radius: 3px;
            }
        """)
        self.attempt_spin.valueChanged.connect(self.on_attempts_changed)
        control_layout.addWidget(self.attempt_spin)
        
        control_layout.addSpacing(20)
        
        self.report_btn = QPushButton("Создать отчет")
        self.report_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        self.report_btn.clicked.connect(self.make_report)
        self.report_btn.setEnabled(False)
        control_layout.addWidget(self.report_btn)
        
        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setEnabled(False)
        control_layout.addWidget(self.clear_btn)
        
        main_layout.addWidget(control_panel)
    
    def init_test_list(self):
        """Инициализация списка тестов"""
        self.tests = [
            {
                'name': 'Простая реакция',
                'class': SimpleReactionTest,
                'category': 'Базовые',
                'description': 'Измерение времени простой реакции на визуальный стимул',
                'instructions': """ИНСТРУКЦИЯ: ПРОСТАЯ РЕАКЦИЯ

1. Нажмите и удерживайте кнопку «СТАРТ»
2. Через случайную задержку (0.5-2.0 сек) появится стимул
3. Быстро отпустите кнопку «СТАРТ»
4. Немедленно кликните на появившийся стимул

Цель: Измерить время вашей простой реакции на визуальный стимул."""
            },
            {
                'name': 'Реакция выбора',
                'class': ChoiceReactionTest,
                'category': 'Базовые',
                'description': 'Реакция на правильный стимул среди нескольких',
                'instructions': """ИНСТРУКЦИЯ: РЕАКЦИЯ ВЫБОРА

1. Нажмите и удерживайте кнопку «СТАРТ»
2. Появится образец (форма и цвет)
3. Появятся 2 стимула - один совпадает с образцом
4. Выберите стимул, полностью совпадающий с образцом

Цель: Измерить время реакции при необходимости выбора."""
            },
            {
                'name': 'Сложный выбор',
                'class': ComplexChoiceTest,
                'category': 'Базовые',
                'description': 'Выбор среди множества дистракторов',
                'instructions': """ИНСТРУКЦИЯ: СЛОЖНЫЙ ВЫБОР

1. Нажмите и удерживайте кнопку «СТАРТ»
2. Запомните образец (форма и цвет)
3. Появятся 3 стимула с дистракторами
4. Выберите точную копию образца

Цель: Оценить способность к выбору среди помех."""
            },
            {
                'name': 'Реакция на движущийся объект',
                'class': MovingObjectReactionTest,
                'category': 'Пространственные',
                'description': 'Точность реакции на движущуюся цель',
                'instructions': """ИНСТРУКЦИЯ: РЕАКЦИЯ НА ДВИЖУЩИЙСЯ ОБЪЕКТ

1. Объект движется по экрану по предсказуемой траектории
2. Когда объект попадает в целевую зону, быстро кликните на него
3. Старайтесь кликнуть точно в момент нахождения в зоне

Цель: Оценить точность временной и пространственной реакции."""
            },
            {
                'name': 'Предвидение траектории',
                'class': TrajectoryPredictionTest,
                'category': 'Пространственные',
                'description': 'Предсказание позиции движущегося объекта',
                'instructions': """ИНСТРУКЦИЯ: ПРЕДВИДЕНИЕ ТРАЕКТОРИИ

1. Нажмите и удерживайте кнопку «СТАРТ»
2. Наблюдайте за движением объекта 3-5 секунд
3. Объект исчезнет - вам нужно предсказать его позицию через 1.5 секунды
4. Кликните в то место, где, по вашему мнению, будет находиться объект

Цель: Оценить способность к экстраполяции движения."""
            },
            {
                'name': 'Слежение',
                'class': TrackingFollowingTest,
                'category': 'Пространственные',
                'description': 'Слежение за движущимся объектом',
                'instructions': """ИНСТРУКЦИЯ: СЛЕЖЕНИЕ

1. Удерживайте курсор мыши внутри движущегося круга
2. Круг будет менять направление и скорость
3. Скорость увеличивается каждые 2 секунды
4. Тест завершится, когда круг станет слишком быстрым

Цель: Оценить способность к слежению за движущимся объектом."""
            },
            {
                'name': 'Переключение внимания',
                'class': AttentionSwitchingTest,
                'category': 'Когнитивные',
                'description': 'Тест на когнитивную гибкость',
                'instructions': """ИНСТРУКЦИЯ: ПЕРЕКЛЮЧЕНИЕ ВНИМАНИЯ

1. В начале теста нужно кликать на КРУГИ
2. После определенного момента правило меняется
3. После изменения нужно кликать на КВАДРАТЫ
4. Каждое испытание имеет ограничение по времени (3 сек)

Цель: Оценить способность к переключению внимания между задачами."""
            },
            {
                'name': 'Таблицы Горбова-Шульте (с подсказкой)',
                'class': GorbovShulteTest,
                'category': 'Когнитивные',
                'description': 'Поиск чисел с подсказкой следующего числа',
                'instructions': """ИНСТРУКЦИЯ: ТАБЛИЦЫ ГОРБОВА-ШУЛЬТЕ (С ПОДСКАЗКОЙ)

1. Найдите числа в последовательности:
   - Красная 1 → Черная 24 → Красная 2 → Черная 23 → ...
   - Красные числа: 1-25 (все 25 чисел)
   - Черные числа: 24-1 (24 числа, без 25)

2. Следующее число будет подсвечено на таблице
3. Кликайте на подсвеченные числа в правильной последовательности

Цель: Оценить переключение внимания с визуальной поддержкой."""
            },
            {
                'name': 'Таблицы Горбова-Шульте (без подсказки)',
                'class': GorbovShulteTestNoHint,
                'category': 'Когнитивные',
                'description': 'Поиск чисел без подсказки - строгий режим',
                'instructions': """ИНСТРУКЦИЯ: ТАБЛИЦЫ ГОРБОВА-Шульте (БЕЗ ПОДСКАЗКИ)

1. Найдите числа в последовательности:
   - Красная 1 → Черная 24 → Красная 2 → Черная 23 → ...
   - Красные числа: 1-25 (все 25 чисел)
   - Черные числа: 24-1 (24 числа, без 25)

2. НИКАКИХ ПОДСКАЗОК - следующее число не подсвечивается
3. Запоминайте последовательность самостоятельно
4. Кликайте на числа в правильном порядке

Цель: Оценить рабочую память и переключение внимания без поддержки."""
            },
            {
                'name': 'Тест Струпа',
                'class': StroopTest,
                'category': 'Когнитивные',
                'description': 'Измерение интерференции при обработке информации',
                'instructions': """ИНСТРУКЦИЯ: ТЕСТ СТРУПА

1. В каждом испытании будет показано слово, обозначающее цвет
2. Слово будет окрашено в какой-либо цвет
3. В зависимости от инструкции:
   - Либо читайте слово (что написано)
   - Либо называйте цвет (каким цветом написано)

4. Выберите правильный цвет из предложенных вариантов

Цель: Измерить интерференцию между чтением и распознаванием цвета."""
            },
            {
                'name': 'Различение размеров',
                'class': SizeDiscriminationTest,
                'category': 'Перцептивные',
                'description': 'Определение наибольшего круга среди нескольких',
                'instructions': """ИНСТРУКЦИЯ: РАЗЛИЧЕНИЕ РАЗМЕРОВ

1. Нажмите СТАРТ - появится несколько кругов разного размера
2. Выберите круг НАИБОЛЬШЕГО размера
3. Сложность автоматически адаптируется к вашей точности
4. Всего 8 попыток

Цель: Оценить точность визуального различения размеров."""
            },
            {
                'name': 'Различение цветов',
                'class': ColorDiscriminationTest,
                'category': 'Перцептивные',
                'description': 'Нахождение квадрата заданного цвета среди похожих',
                'instructions': """ИНСТРУКЦИЯ: РАЗЛИЧЕНИЕ ЦВЕТОВ

1. Нажмите СТАРТ - появится несколько квадратов разных оттенков
2. Сверху указан искомый цвет
3. Выберите квадрат указанного цвета
4. Сложность автоматически адаптируется к вашей точностью

Цель: Оценить точность цветового различения."""
            },
            {
                'name': 'Оперативная память',
                'class': WorkingMemoryTest,
                'category': 'Память',
                'description': 'Запоминание чисел и цветов с двойной задачей',
                'instructions': """ИНСТРУКЦИЯ: ОПЕРАТИВНАЯ ПАМЯТЬ

1. Нажмите СТАРТ - появится таблица 5×5 с числами разных цветов
2. Запомните числа и их цвета за 5 секунд
3. Затем таблица скроется
4. Сначала выберите все клетки с указанным цветом
5. Затем выберите все клетки с чётными/нечётными числами

Цель: Оценить объём оперативной памяти и способность к двойной задаче."""
            },
            {
                'name': 'Комбинированный A',
                'class': CombinedTestA,
                'category': 'Комбинированные',
                'description': 'Комбинация простой и сложной реакции',
                'instructions': """ИНСТРУКЦИЯ: КОМБИНИРОВАННЫЙ ТЕСТ A

1. Появятся два движущихся объектов
2. Один из них соответствует образцу
3. Следите за обоими объектами
4. Выберите правильный объект в нужный момент

Цель: Оценить распределение внимания между движущимися объектами."""
            },
            {
                'name': 'Комбинированный B',
                'class': CombinedTestB,
                'category': 'Комбинированные',
                'description': 'Продвинутая комбинация тестов',
                'instructions': """ИНСТРУКЦИЯ: КОМБИНИРОВАННЫЙ ТЕСТ B

1. Начинается как простой тест
2. Через 1.5-2.5 секунды правила меняются
3. Необходимо быстро переключиться на новые стимулы
4. Выберите новый целевой стимул

Цель: Оценить способность к быстрому переключению в динамических условиях."""
            }
        ]
        
        self.load_tests_for_category('Все')
    
    def on_tab_changed(self, index):
        category = self.tab_widget.tabText(index)
        self.load_tests_for_category(category)
    
    def load_tests_for_category(self, category):
        _, layout, _ = self.test_tabs[category]
        
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if category == 'Все':
            filtered_tests = self.tests
        else:
            filtered_tests = [t for t in self.tests if t['category'] == category]
        
        row = 0
        col = 0
        max_cols = 4
        
        colors = {
            'Базовые': '#3498DB',
            'Пространственные': '#9B59B6',
            'Когнитивные': '#2ECC71',
            'Перцептивные': '#E67E22',
            'Память': '#1ABC9C',
            'Комбинированные': '#E74C3C'
        }
        
        for test_info in filtered_tests:
            color = colors.get(test_info['category'], '#3498DB')
            
            card = TestCard(
                title=test_info['name'],
                description=test_info['description'],
                category=test_info['category'],
                color=color
            )
            
            def create_handler(t=test_info):
                return lambda: self.start_test(t)
            
            card.clicked.connect(create_handler())
            
            layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def start_test(self, test_info):
        dialog = InstructionsDialog(
            test_info['name'],
            test_info['instructions'],
            self.attempts,
            self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.test_window = TestWindow(
                test_info['class'],
                test_info['name'],
                self.attempts,
                self
            )
            self.test_window.show()
    
    def on_attempts_changed(self, value):
        self.attempts = value
    
    def on_test_complete(self, result):
        if isinstance(result, dict):
            self.all_results.append(result)
        
        if hasattr(self, 'test_window'):
            try:
                self.test_window.close()
                self.test_window.deleteLater()
            except:
                pass
            finally:
                try:
                    delattr(self, 'test_window')
                except:
                    pass
        
        self.update_stats()
        
        QMessageBox.information(
            self,
            "Тест завершен",
            f"Выполнено {self.attempts} попыток.\nРезультаты сохранены."
        )
    
    def update_stats(self):
        total_tests = len(set(
            r.get('test_name', '') 
            for r in self.all_results 
            if isinstance(r, dict)
        ))
        
        total_attempts = 0
        successful_attempts = 0
        
        for r in self.all_results:
            if isinstance(r, dict):
                if 'attempt_results' in r:
                    attempts = r['attempt_results']
                    total_attempts += len(attempts)
                    successful_attempts += sum(1 for a in attempts if isinstance(a, dict) and a.get('correct', False))
                elif r.get('correct', False):
                    total_attempts += 1
                    successful_attempts += 1
                else:
                    total_attempts += 1
        
        if total_attempts > 0:
            accuracy = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0
            self.stats_label.setText(
                f"Тестов: {total_tests}, Попыток: {total_attempts}, Точность: {accuracy:.1f}%"
            )
            
            self.report_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
        else:
            self.stats_label.setText("Готов к тестированию")
            self.report_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
    
    def clear_results(self):
        reply = QMessageBox.question(
            self,
            "Очистка",
            "Очистить все результаты?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.all_results.clear()
            self.update_stats()
    
    def make_report(self):
        if not self.all_results:
            QMessageBox.warning(self, "Нет данных", "Сначала выполните тесты.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/report_{timestamp}.pdf"
        csv_path = f"reports/raw_data_{timestamp}.csv"
        
        os.makedirs("reports", exist_ok=True)
        
        try:
            success = generate_report(
                self.all_results,
                output_path,
                csv_path,
                self.font_family
            )
            
            if success:
                analysis = self.analyzer.analyze_comprehensive_performance(self.all_results)
                self.progress_tracker.add_session(analysis)
                
                QMessageBox.information(
                    self,
                    "Отчет создан",
                    f"Отчет сохранен:\n{output_path}\n\nCSV данные: {csv_path}"
                )
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать отчет.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")


class TestWindow(QMainWindow):
    """Окно выполнения теста"""
    
    def __init__(self, test_class, test_name, attempts, main_window):
        super().__init__()
        self.test_class = test_class
        self.test_name = test_name
        self.attempts = attempts
        self.main_window = main_window
        
        self.setWindowTitle(test_name)
        self.resize(1000, 700)
        
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        info_panel = QFrame()
        info_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #DDDDDD;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        info_layout = QHBoxLayout(info_panel)
        
        title_label = QLabel(self.test_name)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2C3E50;
            }
        """)
        info_layout.addWidget(title_label)
        
        info_layout.addStretch()
        
        self.attempt_label = QLabel(f"Попытка: 1/{self.attempts}")
        self.attempt_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #3498DB;
                background-color: #E8F4FC;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        info_layout.addWidget(self.attempt_label)
        
        layout.addWidget(info_panel)
        
        test_area = QFrame()
        test_area.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #DDDDDD;
                border-radius: 5px;
            }
        """)
        
        test_layout = QVBoxLayout(test_area)
        test_layout.setContentsMargins(0, 0, 0, 0)
        
        self.test_runner = TestRunner(
            self.test_class,
            self.test_name,
            self.attempts,
            self.main_window,
            test_area
        )
        test_layout.addWidget(self.test_runner)
        
        layout.addWidget(test_area, 1)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def update_attempt_display(self, current, total):
        self.attempt_label.setText(f"Попытка: {current}/{total}")
    
    def closeEvent(self, event):
        if hasattr(self.test_runner, 'stop_all_timers'):
            self.test_runner.stop_all_timers()
        
        try:
            self.test_runner.deleteLater()
        except:
            pass
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    icon_path = "resources/icon.png"
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
