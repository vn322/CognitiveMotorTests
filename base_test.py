from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

class BaseTest(QWidget):
    """Базовый класс для всех тестов"""
    test_finished = pyqtSignal()
    attempt_finished = pyqtSignal()
    result_ready = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        # Если родитель не является QWidget, устанавливаем parent=None
        if parent is not None and not isinstance(parent, QWidget):
            super().__init__(None)
        else:
            super().__init__(parent)
        
    def start_test(self, total_attempts):
        """Начать тест с указанным количеством попыток"""
        self.total_attempts = total_attempts
        self.current_attempt = 0
        self.results = []
        
    def start_attempt(self):
        """Начать очередную попытку"""
        self.current_attempt += 1
        
    def get_results(self):
        """Получить результаты теста"""
        return self.results
        
    def reset(self):
        """Сбросить состояние теста"""
        self.current_attempt = 0
        self.results = []