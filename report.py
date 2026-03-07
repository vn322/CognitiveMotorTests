# report.py 
import sys
import os
import json
import csv
import math
from datetime import datetime
from collections import defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch, cm

from cognitive_metrics import CognitiveMotorAnalyzer


def get_font_path():
    """Получить корректный путь к шрифту при работе в exe или исходном коде"""
    if getattr(sys, 'frozen', False):
        # Работаем в скомпилированном приложении
        base_path = sys._MEIPASS
    else:
        # Работаем в исходном коде
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Пробуем разные пути к шрифту
    font_paths = [
        os.path.join(base_path, 'resources', 'DejaVuSans.ttf'),
        os.path.join(base_path, 'DejaVuSans.ttf'),
        os.path.join('.', 'resources', 'DejaVuSans.ttf'),
        os.path.join('.', 'DejaVuSans.ttf'),
        os.path.join(os.path.dirname(sys.executable), 'resources', 'DejaVuSans.ttf'),
        os.path.join(os.path.dirname(sys.executable), 'DejaVuSans.ttf'),
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path
    
    # Если шрифт не найден, возвращаем None
    return None


def calculate_std(values):
    """Рассчитать стандартное отклонение"""
    if len(values) < 2:
        return 0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def calculate_stability(values):
    """Рассчитать стабильность (чем меньше отклонение, тем выше стабильность)"""
    if len(values) < 2:
        return 100  # Если одна попытка - идеальная стабильность
    
    std = calculate_std(values)
    mean = sum(values) / len(values)
    
    if mean == 0:
        return 0
    
    # Коэффициент вариации
    cv = std / mean
    
    # Преобразуем в процент стабильности
    stability = max(0, 100 - (cv * 100))
    return min(100, stability)


def calculate_spatial_accuracy(distances):
    """Рассчитать пространственную точность по расстоянию от центра"""
    if not distances:
        return 0
    
    avg_distance = sum(distances) / len(distances)
    
    # Чем меньше расстояние, тем выше точность
    if avg_distance < 5:
        return 100
    elif avg_distance < 10:
        return 95
    elif avg_distance < 15:
        return 90
    elif avg_distance < 20:
        return 85
    elif avg_distance < 25:
        return 80
    elif avg_distance < 30:
        return 75
    elif avg_distance < 35:
        return 70
    elif avg_distance < 40:
        return 65
    elif avg_distance < 45:
        return 60
    elif avg_distance < 50:
        return 55
    else:
        return 50


def calculate_spatial_precision(distances):
    """Рассчитать пространственную точность для других тестов"""
    if not distances:
        return 0
    avg_distance = sum(distances) / len(distances)
    precision = max(0, 100 - (avg_distance / 5))
    return min(100, precision)


def calculate_relevant_metrics(results, test_name):
    """Рассчитать релевантные метрики для конкретного теста"""
    metrics = {}
    
    if not results:
        return metrics
    
    # Получаем все попытки из результатов
    all_attempts = []
    successful_attempts = []
    failed_attempts = []
    
    for r in results:
        if isinstance(r, dict):
            if 'attempt_results' in r and r['attempt_results']:
                for attempt in r['attempt_results']:
                    if isinstance(attempt, dict):
                        all_attempts.append(attempt)
                        if attempt.get('correct', False):
                            successful_attempts.append(attempt)
                        else:
                            failed_attempts.append(attempt)
            else:
                all_attempts.append(r)
                if r.get('correct', False):
                    successful_attempts.append(r)
                else:
                    failed_attempts.append(r)
    
    if not all_attempts:
        return metrics
    
    # Общие метрики для всех тестов
    total_attempts = len(all_attempts)
    successful_count = len(successful_attempts)
    failed_count = len(failed_attempts)
    accuracy = (successful_count / total_attempts * 100) if total_attempts > 0 else 0
    
    metrics['total_attempts'] = total_attempts
    metrics['successful_attempts'] = successful_count
    metrics['failed_attempts'] = failed_count
    metrics['accuracy'] = accuracy
    
    # ===== БАЗОВЫЕ РЕАКЦИОННЫЕ ТЕСТЫ =====
    # Простая реакция, Реакция выбора, Сложный выбор - ОДИНАКОВЫЕ МЕТРИКИ
    if test_name in ['Простая реакция', 'Реакция выбора', 'Сложный выбор']:
        # 1. ВРЕМЯ ПРИНЯТИЯ РЕШЕНИЙ (латентное время) - ТОЛЬКО УСПЕШНЫЕ
        decision_times = []
        for r in successful_attempts:
            latency = r.get('latency')
            if latency is not None and latency > 0:
                decision_times.append(latency)
        
        if decision_times:
            metrics['avg_decision_time'] = sum(decision_times) / len(decision_times)
            metrics['decision_time_std'] = calculate_std(decision_times)
            metrics['min_decision_time'] = min(decision_times)
            metrics['max_decision_time'] = max(decision_times)
        
        # 2. МОТОРНОЕ ВРЕМЯ - ТОЛЬКО УСПЕШНЫЕ
        motor_times = []
        for r in successful_attempts:
            motor_time = r.get('motor_time')
            if motor_time is not None and motor_time > 0:
                motor_times.append(motor_time)
        
        if motor_times:
            metrics['avg_motor_time'] = sum(motor_times) / len(motor_times)
            metrics['motor_time_std'] = calculate_std(motor_times)
        
        # 3. ОБЩЕЕ ВРЕМЯ РЕАКЦИИ - ТОЛЬКО УСПЕШНЫЕ
        total_reaction_times = []
        for r in successful_attempts:
            total_rt = r.get('total_rt')
            if total_rt is not None and total_rt > 0:
                total_reaction_times.append(total_rt)
        
        if total_reaction_times:
            metrics['avg_total_reaction_time'] = sum(total_reaction_times) / len(total_reaction_times)
            metrics['total_reaction_time_std'] = calculate_std(total_reaction_times)
        
        # 4. ПРОСТРАНСТВЕННАЯ ТОЧНОСТЬ (по радиусу от центра)
        distances = []
        for r in successful_attempts:
            distance = r.get('distance_from_center')
            if distance is not None and distance >= 0:
                distances.append(distance)
        
        if distances:
            metrics['avg_distance_from_center'] = sum(distances) / len(distances)
            metrics['distance_std'] = calculate_std(distances)
            metrics['spatial_accuracy'] = calculate_spatial_accuracy(distances)
        
        # 5. СТАБИЛЬНОСТЬ (по стандартному отклонению времени принятия решений)
        if decision_times:
            metrics['stability'] = calculate_stability(decision_times)
        
        # 6. АНАЛИЗ ОШИБОК
        if failed_attempts:
            # Причины ошибок
            error_types = {
                'too_fast': 0,     # Антиципация (<100 мс)
                'too_slow': 0,     # Пропуск (>1000 мс)
                'wrong_choice': 0, # Неправильный выбор (только для выбора)
                'missed': 0        # Промах (клик вне цели)
            }
            
            for r in failed_attempts:
                latency = r.get('latency', 0)
                total_rt = r.get('total_rt', 0)
                distance = r.get('distance_from_center', float('inf'))
                
                if latency < 0.1:  # <100 мс - антиципация
                    error_types['too_fast'] += 1
                elif total_rt > 1.0:  # >1000 мс - пропуск
                    error_types['too_slow'] += 1
                elif distance > 50:  # >50 пикселей - промах
                    error_types['missed'] += 1
                else:
                    # Для тестов выбора - ошибка выбора
                    if test_name in ['Реакция выбора', 'Сложный выбор']:
                        error_types['wrong_choice'] += 1
                    else:
                        error_types['missed'] += 1
            
            metrics['error_analysis'] = error_types
            metrics['total_errors'] = failed_count
    
    # ===== ПРОСТРАНСТВЕННЫЕ ТЕСТЫ =====
    elif test_name == 'Реакция на движущийся объект':
        timing_errors = []
        distances = []
        
        for r in all_attempts:
            timing_delay = r.get('timing_delay')
            distance = r.get('distance_from_center')
            
            if timing_delay is not None:
                timing_errors.append(timing_delay)
            if distance is not None:
                distances.append(distance)
        
        if timing_errors:
            metrics['avg_timing_error'] = sum(timing_errors) / len(timing_errors)
        
        if distances:
            metrics['avg_spatial_error'] = sum(distances) / len(distances)
    
    elif test_name == 'Предвидение траектории':
        accuracies = []
        errors = []
        
        for r in all_attempts:
            pred_accuracy = r.get('prediction_accuracy')
            pred_error = r.get('prediction_error_px')
            
            if pred_accuracy is not None:
                accuracies.append(pred_accuracy)
            if pred_error is not None:
                errors.append(pred_error)
        
        if accuracies:
            metrics['avg_prediction_accuracy'] = sum(accuracies) / len(accuracies)
        
        if errors:
            metrics['avg_prediction_error'] = sum(errors) / len(errors)
    
    elif test_name == 'Слежение':
        distances = []
        hit_rates = []
        
        for r in all_attempts:
            avg_dist = r.get('avg_distance_px')
            hit_rate = r.get('hit_rate_50_percent')
            
            if avg_dist is not None:
                distances.append(avg_dist)
            if hit_rate is not None:
                hit_rates.append(hit_rate)
        
        if distances:
            metrics['avg_tracking_error'] = sum(distances) / len(distances)
        
        if hit_rates:
            metrics['avg_hit_rate'] = sum(hit_rates) / len(hit_rates)
    
    # ===== КОГНИТИВНАЯ ГИБКОСТЬ =====
    elif test_name == 'Переключение внимания':
        switch_costs = []
        accuracies = []
        
        for r in all_attempts:
            cost = r.get('switch_cost')
            accuracy = r.get('accuracy')
            
            if cost is not None:
                switch_costs.append(cost)
            if accuracy is not None:
                accuracies.append(accuracy)
        
        if switch_costs:
            metrics['avg_switch_cost'] = sum(switch_costs) / len(switch_costs)
        
        if accuracies:
            metrics['avg_attention_accuracy'] = sum(accuracies) / len(accuracies)
    
    # ===== ОПЕРАТИВНАЯ ПАМЯТЬ =====
    elif test_name == 'Оперативная память':
        accuracies = []
        correct_counts = []
        total_trials_list = []
        
        for r in all_attempts:
            accuracy = r.get('accuracy')
            correct_count = r.get('correct_count')
            total_trials = r.get('total_trials')
            
            if accuracy is not None:
                accuracies.append(accuracy)
            if correct_count is not None:
                correct_counts.append(correct_count)
            if total_trials is not None:
                total_trials_list.append(total_trials)
        
        if accuracies:
            metrics['memory_accuracy'] = sum(accuracies) / len(accuracies)
        
        if correct_counts:
            metrics['avg_correct_items'] = sum(correct_counts) / len(correct_counts)
        
        if total_trials_list:
            total_trials_sum = sum(total_trials_list)
            total_correct_sum = sum(correct_counts) if correct_counts else 0
            if total_trials_sum > 0:
                metrics['memory_efficiency'] = (total_correct_sum / total_trials_sum) * 100
    
    # ===== ВОСПРИЯТИЕ =====
    elif test_name == 'Различение размеров':
        accuracies = []
        size_errors = []
        
        for r in all_attempts:
            accuracy = r.get('accuracy')
            avg_error = r.get('avg_size_error')
            
            if accuracy is not None:
                accuracies.append(accuracy)
            if avg_error is not None:
                size_errors.append(abs(avg_error))
        
        if accuracies:
            metrics['size_discrimination_accuracy'] = sum(accuracies) / len(accuracies)
        
        if size_errors:
            metrics['avg_size_error'] = sum(size_errors) / len(size_errors)
    
    elif test_name == 'Различение цветов':
        accuracies = []
        
        for r in all_attempts:
            accuracy = r.get('accuracy')
            if accuracy is not None:
                accuracies.append(accuracy)
        
        if accuracies:
            metrics['color_discrimination_accuracy'] = sum(accuracies) / len(accuracies)
    
    # ===== ТЕСТ СТРУПА =====
    elif test_name == 'Тест Струпа':
        stroop_effects = []
        accuracies = []
        
        for r in all_attempts:
            effect = r.get('stroop_effect')
            accuracy = r.get('accuracy')
            
            if effect is not None:
                stroop_effects.append(effect)
            if accuracy is not None:
                accuracies.append(accuracy)
        
        if stroop_effects:
            metrics['avg_stroop_effect'] = sum(stroop_effects) / len(stroop_effects)
        
        if accuracies:
            metrics['stroop_accuracy'] = sum(accuracies) / len(accuracies)
    
    # ===== ТАБЛИЦЫ ГОРБОВА-ШУЛЬТЕ =====
    elif 'Таблицы Горбова-Шульте' in test_name:
        search_times = []
        accuracies = []
        
        for r in all_attempts:
            rt = r.get('total_rt')
            accuracy = r.get('accuracy')
            
            if rt is not None and rt > 0:
                search_times.append(rt)
            if accuracy is not None:
                accuracies.append(accuracy)
        
        if search_times:
            metrics['avg_search_time'] = sum(search_times) / len(search_times)
        
        if accuracies:
            metrics['search_accuracy'] = sum(accuracies) / len(accuracies)
    
    # ===== КОМБИНИРОВАННЫЕ ТЕСТЫ =====
    elif test_name in ['Комбинированный A', 'Комбинированный B']:
        latencies = []
        distances = []
        
        for r in successful_attempts:
            latency = r.get('latency')
            distance = r.get('distance_from_center')
            
            if latency is not None and latency > 0:
                latencies.append(latency)
            if distance is not None:
                distances.append(distance)
        
        if latencies:
            metrics['avg_combined_time'] = sum(latencies) / len(latencies)
        
        if distances:
            metrics['multi_task_precision'] = calculate_spatial_precision(distances)
    
    return metrics


def generate_report(all_results, output_path, csv_path, font_family="DejaVuSans"):
    # === CSV с UTF-8-BOM для Excel ===
    if all_results:
        try:
            all_fields = set()
            
            for test_result in all_results:
                if isinstance(test_result, dict):
                    if 'attempt_results' in test_result:
                        for attempt in test_result['attempt_results']:
                            if isinstance(attempt, dict):
                                # Удаляем anticipation и delay
                                attempt_copy = attempt.copy()
                                if 'anticipation' in attempt_copy:
                                    del attempt_copy['anticipation']
                                if 'delay' in attempt_copy:
                                    del attempt_copy['delay']
                                all_fields.update(attempt_copy.keys())
                        all_fields.update(['test_name', 'attempts'])
                    else:
                        result_copy = test_result.copy()
                        if 'anticipation' in result_copy:
                            del result_copy['anticipation']
                        if 'delay' in result_copy:
                            del result_copy['delay']
                        all_fields.update(result_copy.keys())
            
            primary_fields = [
                'test_name', 'attempt_number', 'total_attempts',
                'timestamp', 'latency', 'motor_time', 'total_rt', 
                'correct', 'click_x', 'click_y', 'distance_from_center',
                'timing_delay', 'trajectory_type', 'speed',
                'avg_pre_switch', 'avg_post_switch', 'switch_cost',
                'rule_changed', 'prediction_accuracy', 'prediction_error_px',
                'observation_time', 'avg_distance_px', 'hit_rate_50_percent',
                'accuracy', 'correct_count', 'total_trials',
                'avg_size_error', 'all_errors', 'avg_difficulty',
                'stroop_effect', 'avg_congruent', 'avg_incongruent',
                'memory_load', 'target_color', 'target_parity',
                'error_type', 'error_reason',  # ДОБАВЛЕНО
                'target_shape', 'target_color_info', 'total_stimuli'  # ДОБАВЛЕНО
            ]
            
            mandatory_fields = ['test_name', 'attempt_number', 'total_attempts', 'timestamp']
            simple_fields = mandatory_fields.copy()
            
            for pf in primary_fields:
                if pf not in simple_fields and pf in all_fields:
                    simple_fields.append(pf)
            
            for f in sorted(all_fields):
                if f not in simple_fields and f not in ['attempt_results', 'trial_results', 'all_results']:
                    if f not in ['response_times', 'errors', 'timestamps', 'anticipation', 'delay']:
                        simple_fields.append(f)
            
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=simple_fields)
                writer.writeheader()
                
                timestamp_counter = 0
                
                for test_result in all_results:
                    if isinstance(test_result, dict):
                        test_name = test_result.get('test_name', 'Unknown')
                        total_attempts = test_result.get('attempts', 1)
                        
                        if 'attempt_results' in test_result and test_result['attempt_results']:
                            for i, attempt in enumerate(test_result['attempt_results']):
                                if isinstance(attempt, dict):
                                    row_data = {}
                                    
                                    row_data['test_name'] = test_name
                                    row_data['attempt_number'] = i + 1
                                    row_data['total_attempts'] = total_attempts
                                    row_data['timestamp'] = f"{timestamp_counter:06d}"
                                    timestamp_counter += 1
                                    
                                    for key, value in attempt.items():
                                        if key in simple_fields and key not in ['anticipation', 'delay']:
                                            if isinstance(value, (list, dict, tuple)):
                                                row_data[key] = json.dumps(value, ensure_ascii=False)
                                            else:
                                                row_data[key] = value
                                    
                                    writer.writerow(row_data)
                        else:
                            row_data = {}
                            row_data['test_name'] = test_name
                            row_data['attempt_number'] = 1
                            row_data['total_attempts'] = 1
                            row_data['timestamp'] = f"{timestamp_counter:06d}"
                            timestamp_counter += 1
                            
                            for key, value in test_result.items():
                                if key in simple_fields and key not in ['anticipation', 'delay']:
                                    if isinstance(value, (list, dict, tuple)):
                                        row_data[key] = json.dumps(value, ensure_ascii=False)
                                    else:
                                        row_data[key] = value
                            
                            writer.writerow(row_data)
                            
            print(f"CSV файл создан: {csv_path}, записей: {timestamp_counter}")
        except Exception as e:
            print(f"Ошибка при создании CSV: {e}")
            import traceback
            traceback.print_exc()

    # === Комплексный анализ ===
    analyzer = CognitiveMotorAnalyzer()
    comprehensive_analysis = analyzer.analyze_comprehensive_performance(all_results)

    # === PDF ===
    normal_font = 'Helvetica'
    
    try:
        font_path = get_font_path()
        
        if font_path and os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('DejaVu', font_path))
                normal_font = 'DejaVu'
                print(f"Шрифт успешно загружен: {font_path}")
            except Exception as font_error:
                print(f"Ошибка регистрации шрифта {font_path}: {font_error}")
                # Пробуем использовать системные шрифты
                try:
                    # Для Windows пробуем Arial
                    import platform
                    if platform.system() == 'Windows':
                        pdfmetrics.registerFont(TTFont('DejaVu', 'Arial'))
                        normal_font = 'DejaVu'
                        print("Используется системный шрифт Arial")
                except:
                    pass
        else:
            print(f"Шрифт не найден по пути: {font_path}")
            # Пробуем использовать встроенный шрифт Helvetica
            try:
                from reportlab.pdfbase.pdfmetrics import registerFontFamily
                registerFontFamily('Helvetica', normal='Helvetica', bold='Helvetica-Bold', 
                                 italic='Helvetica-Oblique', boldItalic='Helvetica-BoldOblique')
                print("Используется встроенный шрифт Helvetica")
            except:
                pass
    except Exception as e:
        print(f"Общая ошибка при работе со шрифтами: {e}")
        import traceback
        traceback.print_exc()
    
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Создаем собственные стили
    style_title = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontName=normal_font,
        fontSize=16,
        alignment=1,
        spaceAfter=20,
        textColor=colors.HexColor('#2C3E50')
    )
    
    style_heading = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName=normal_font,
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#3498DB')
    )
    
    style_subheading = ParagraphStyle(
        'Subheading',
        parent=styles['Heading3'],
        fontName=normal_font,
        fontSize=12,
        spaceAfter=8,
        spaceBefore=15,
        textColor=colors.HexColor('#7F8C8D')
    )
    
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=normal_font,
        fontSize=10,
        leading=12,
        spaceAfter=6
    )
    
    style_small = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontName=normal_font,
        fontSize=9,
        leading=11,
        textColor=colors.gray,
        spaceAfter=4
    )
    
    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName=normal_font,
        fontSize=8,
        alignment=1,
        textColor=colors.white,
        leading=10
    )
    
    style_highlight = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontName=normal_font,
        fontSize=11,
        leading=13,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=8,
        spaceBefore=8
    )
    
    story = []
    
    # Заголовок отчета
    story.append(Paragraph("Тестирование когнитивно-моторной подготовленности ", style_title))
    story.append(Paragraph("Комплексный аналитический отчёт", style_heading))
    story.append(Spacer(1, 10))
    
    # Дата и время генерации
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph(f"Дата генерации: {timestamp}", style_small))
    story.append(Spacer(1, 20))
    
    # === КОМПЛЕКСНЫЙ АНАЛИЗ ПОДГОТОВЛЕННОСТИ ===
    story.append(Paragraph("Оценка когнитивно-моторной подготовленности", style_heading))
    story.append(Spacer(1, 15))
    
    # Общий балл
    overall_score = comprehensive_analysis['overall_score']
    story.append(Paragraph(f"Общий балл: {overall_score:.1f}/100", style_subheading))
    
    # Определение уровня
    if overall_score >= 90:
        level = "Профессиональный"
        level_desc = "Высокий уровень когнитивно-моторной подготовленности"
    elif overall_score >= 80:
        level = "Продвинутый"
        level_desc = "Хороший уровень подготовленности"
    elif overall_score >= 60:
        level = "Средний"
        level_desc = "Средний уровень, есть потенциал для развития"
    elif overall_score >= 40:
        level = "Начинающий"
        level_desc = "Базовый уровень, требуется систематическая тренировка"
    else:
        level = "Новичок"
        level_desc = "Начальный уровень, рекомендуется интенсивная тренировка"
    
    story.append(Paragraph(f"Уровень: {level}", style_highlight))
    story.append(Paragraph(level_desc, style_normal))
    story.append(Spacer(1, 20))
    
    # === АНАЛИЗ ПО КАТЕГОРИЯМ ДАННЫХ (ТОЛЬКО ЕСЛИ ЕСТЬ ДАННЫЕ) ===
    story.append(Paragraph("Анализ по категориям навыков", style_subheading))
    
    # Группируем результаты для расчета реальных метрик
    grouped = defaultdict(list)
    for r in all_results:
        if isinstance(r, dict):
            test_name = r.get('test_name', 'Неизвестно')
            grouped[test_name].append(r)
    
    # Определяем категории и соответствующие тесты
    categories_config = {
        'Базовые реакции': {
            'tests': ['Простая реакция', 'Реакция выбора', 'Сложный выбор'],
            'description': 'Скорость и точность реакции на стимулы разной сложности'
        },
        'Пространственные навыки': {
            'tests': ['Реакция на движущийся объект', 'Предвидение траектории', 'Слежение'],
            'description': 'Работа с движущимися объектами и предсказание траекторий'
        },
        'Когнитивная гибкость': {
            'tests': ['Переключение внимания', 'Тест Струпа'],
            'description': 'Способность переключаться между задачами'
        },
        'Восприятие': {
            'tests': ['Различение размеров', 'Различение цветов'],
            'description': 'Точность различения визуальных признаков'
        },
        'Рабочая память': {
            'tests': ['Оперативная память', 'Таблицы Горбова-Шульте (без подсказки)'],
            'description': 'Объем и эффективность кратковременной памяти'
        },
        'Многозадачность': {
            'tests': ['Комбинированный A', 'Комбинированный B'],
            'description': 'Способность выполнять несколько задач одновременно'
        }
    }
    
    # Рассчитываем метрики для каждой категории
    categories_data = []
    for cat_name, config in categories_config.items():
        cat_scores = []
        cat_indicators = []
        
        # Проверяем, есть ли данные для этой категории
        has_data = False
        for test_name in config['tests']:
            if test_name in grouped and grouped[test_name]:
                has_data = True
                break
        
        if not has_data:
            # Если данных нет - не показываем категорию
            continue
        
        # Собираем данные для категории
        for test_name in config['tests']:
            if test_name in grouped:
                results = grouped[test_name]
                metrics = calculate_relevant_metrics(results, test_name)
                
                # Используем accuracy как основной показатель
                if 'accuracy' in metrics:
                    cat_scores.append(metrics['accuracy'])
                
                # Собираем ключевые показатели
                if test_name in ['Простая реакция', 'Реакция выбора', 'Сложный выбор']:
                    if 'avg_decision_time' in metrics:
                        time_str = f"{metrics['avg_decision_time']:.3f} с"
                        if test_name == 'Простая реакция':
                            cat_indicators.append(f"Простая: {time_str}")
                        elif test_name == 'Реакция выбора':
                            cat_indicators.append(f"Выбор: {time_str}")
                        else:
                            cat_indicators.append(f"Сложный: {time_str}")
                
                elif test_name == 'Оперативная память' and 'memory_accuracy' in metrics:
                    cat_indicators.append(f"Память: {metrics['memory_accuracy']:.1f}%")
        
        # Рассчитываем средний балл для категории
        if cat_scores:
            avg_score = sum(cat_scores) / len(cat_scores)
            
            # Определяем оценку
            if avg_score >= 80:
                rating = "Отлично"
            elif avg_score >= 60:
                rating = "Хорошо"
            elif avg_score >= 40:
                rating = "Удовлетворительно"
            else:
                rating = "Требует улучшения"
            
            categories_data.append({
                'name': cat_name,
                'score': avg_score,
                'rating': rating,
                'indicators': cat_indicators[:2],  # Берем первые 2 показателя
                'description': config['description']
            })
    
    # Создаем таблицу только с категориями, где есть данные
    if categories_data:
        category_table_data = [
            ["Категория навыков", "Балл", "Оценка", "Основные показатели"]
        ]
        
        for cat in categories_data:
            category_table_data.append([
                Paragraph(cat['name'], style_normal),
                Paragraph(f"{cat['score']:.1f}", style_normal),
                Paragraph(cat['rating'], style_normal),
                Paragraph("; ".join(cat['indicators']) if cat['indicators'] else "-", style_small)
            ])
        
        col_widths = [2*inch, 0.8*inch, 1.2*inch, 2.5*inch]
        category_table = Table(category_table_data, colWidths=col_widths)
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,-1), normal_font),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9F9')]),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        
        story.append(category_table)
    else:
        story.append(Paragraph("Нет данных для анализа категорий. Пройдите тесты для получения оценки.", style_normal))
    
    story.append(Spacer(1, 25))
    
    # === АНАЛИЗ БАЗОВЫХ РЕАКЦИЙ И ВЛИЯНИЯ СЛОЖНОСТИ ===
    # Сравниваем Простую реакцию, Реакцию выбора и Сложный выбор
    reaction_tests = ['Простая реакция', 'Реакция выбора', 'Сложный выбор']
    reaction_data = []
    
    for test_name in reaction_tests:
        if test_name in grouped:
            results = grouped[test_name]
            metrics = calculate_relevant_metrics(results, test_name)
            
            if 'accuracy' in metrics and 'avg_decision_time' in metrics:
                reaction_data.append({
                    'name': test_name,
                    'test_type': test_name,
                    'accuracy': metrics['accuracy'],
                    'decision_time': metrics['avg_decision_time'],
                    'motor_time': metrics.get('avg_motor_time', 0),
                    'total_reaction_time': metrics.get('avg_total_reaction_time', 0),
                    'spatial_accuracy': metrics.get('spatial_accuracy', 0),
                    'stability': metrics.get('stability', 0),
                    'errors': metrics.get('total_errors', 0)
                })
    
    # Показываем сравнительный анализ только если есть хотя бы 2 теста
    if len(reaction_data) >= 2:
        story.append(Paragraph("Анализ влияния сложности на базовые реакции", style_subheading))
        
        # Объяснение тестов
        story.append(Paragraph("Тесты оценивают одни и те же навыки в усложняющихся условиях:", style_normal))
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=10,
            leftIndent=20,
            firstLineIndent=-20,
            spaceAfter=2
        )
        story.append(Paragraph("• Простая реакция: Реакция на появление стимула", bullet_style))
        story.append(Paragraph("• Реакция выбора: Выбор из 2 вариантов (добавлен 1 дистрактор)", bullet_style))
        story.append(Paragraph("• Сложный выбор: Выбор из 4+ вариантов (много дистракторов)", bullet_style))
        
        story.append(Spacer(1, 10))
        
        # Таблица сравнительного анализа
        comparative_data = [
            ["Тест", "Точность", "Время реш.", "Моторное", "Общее", "Пространств.", "Стаб.", "Ошибки"]
        ]
        
        for test in reaction_data:
            comparative_data.append([
                test['name'],
                f"{test['accuracy']:.1f}%",
                f"{test['decision_time']:.3f} с",
                f"{test['motor_time']:.3f} с" if test['motor_time'] > 0 else "-",
                f"{test['total_reaction_time']:.3f} с" if test['total_reaction_time'] > 0 else "-",
                f"{test['spatial_accuracy']:.0f}%" if test['spatial_accuracy'] > 0 else "-",
                f"{test['stability']:.0f}%",
                str(test['errors'])
            ])
        
        col_widths = [1.3*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.7*inch, 0.6*inch]
        comparative_table = Table(comparative_data, colWidths=col_widths)
        comparative_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,-1), normal_font),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#ECF0F1')]),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 3),
        ]))
        
        story.append(comparative_table)
        
        # Анализ влияния сложности
        story.append(Spacer(1, 15))
        story.append(Paragraph("Анализ влияния усложнения условий:", style_subheading))
        
        if len(reaction_data) == 3:
            simple = next((t for t in reaction_data if t['name'] == 'Простая реакция'), None)
            choice = next((t for t in reaction_data if t['name'] == 'Реакция выбора'), None)
            complex_choice = next((t for t in reaction_data if t['name'] == 'Сложный выбор'), None)
            
            # Анализ времени принятия решений
            if simple and choice:
                time_increase = ((choice['decision_time'] - simple['decision_time']) / simple['decision_time']) * 100
                acc_decrease = simple['accuracy'] - choice['accuracy']
                
                if time_increase > 100:
                    story.append(Paragraph(f"• Добавление выбора из 2 вариантов: Время принятия решений увеличилось на {time_increase:.0f}% (очень сильное влияние)", style_small))
                elif time_increase > 50:
                    story.append(Paragraph(f"• Добавление выбора из 2 вариантов: Время принятия решений увеличилось на {time_increase:.0f}% (сильное влияние)", style_small))
                elif time_increase > 20:
                    story.append(Paragraph(f"• Добавление выбора из 2 вариантов: Время принятия решений увеличилось на {time_increase:.0f}% (умеренное влияние)", style_small))
                else:
                    story.append(Paragraph(f"• Добавление выбора из 2 вариантов: Время принятия решений увеличилось на {time_increase:.0f}% (слабое влияние)", style_small))
                
                if acc_decrease > 15:
                    story.append(Paragraph(f"• Точность снизилась на {acc_decrease:.1f}% (значительное ухудшение)", style_small))
                elif acc_decrease > 5:
                    story.append(Paragraph(f"• Точность снизилась на {acc_decrease:.1f}% (умеренное ухудшение)", style_small))
                elif acc_decrease > 0:
                    story.append(Paragraph(f"• Точность снизилась на {acc_decrease:.1f}% (незначительное ухудшение)", style_small))
                else:
                    story.append(Paragraph(f"• Точность улучшилась на {abs(acc_decrease):.1f}% (хорошая адаптация)", style_small))
            
            if choice and complex_choice:
                time_increase = ((complex_choice['decision_time'] - choice['decision_time']) / choice['decision_time']) * 100
                acc_decrease = choice['accuracy'] - complex_choice['accuracy']
                
                story.append(Paragraph(f"• Переход к выбору из 4+ вариантов: Время увеличилось на {time_increase:.0f}%", style_small))
                
                if acc_decrease > 0:
                    story.append(Paragraph(f"• Дополнительное снижение точности: {acc_decrease:.1f}%", style_small))
            
            # Общие выводы
            story.append(Spacer(1, 10))
            story.append(Paragraph("Ключевые выводы:", style_normal))
            
            # Анализ моторного времени
            if simple and simple['motor_time'] > 0:
                if simple['motor_time'] < 0.1:
                    story.append(Paragraph("• Быстрое моторное выполнение (<100 мс)", style_small))
                elif simple['motor_time'] < 0.2:
                    story.append(Paragraph("• Среднее моторное выполнение (100-200 мс)", style_small))
                else:
                    story.append(Paragraph("• Медленное моторное выполнение (>200 мс)", style_small))
            
            # Анализ пространственной точности
            if simple and simple['spatial_accuracy'] > 0:
                if simple['spatial_accuracy'] > 90:
                    story.append(Paragraph("• Высокая пространственная точность (>90%)", style_small))
                elif simple['spatial_accuracy'] > 80:
                    story.append(Paragraph("• Хорошая пространственная точность (80-90%)", style_small))
                else:
                    story.append(Paragraph("• Низкая пространственная точность (<80%)", style_small))
            
            # Анализ стабильности
            if simple and simple['stability'] > 0:
                if simple['stability'] > 80:
                    story.append(Paragraph("• Высокая стабильность реакции (>80%)", style_small))
                elif simple['stability'] > 60:
                    story.append(Paragraph("• Хорошая стабильность реакции (60-80%)", style_small))
                else:
                    story.append(Paragraph("• Низкая стабильность реакции (<60%)", style_small))
        
        elif len(reaction_data) == 2:
            # Если только 2 теста
            test1, test2 = reaction_data[0], reaction_data[1]
            time_increase = ((test2['decision_time'] - test1['decision_time']) / test1['decision_time']) * 100
            story.append(Paragraph(f"• Усложнение условий: Время принятия решений увеличилось на {time_increase:.0f}%", style_small))
    
    story.append(Spacer(1, 25))
    
    # Рекомендации
    story.append(Paragraph("Персональные рекомендации", style_subheading))
    
    recommendations = comprehensive_analysis.get('recommendations', [])
    if recommendations:
        for rec in recommendations:
            bullet_style = ParagraphStyle(
                'Bullet',
                parent=styles['Normal'],
                fontName=normal_font,
                fontSize=10,
                leftIndent=20,
                firstLineIndent=-20,
                spaceAfter=4
            )
            story.append(Paragraph(f"• {rec}", bullet_style))
    else:
        story.append(Paragraph("Пройдите больше тестов для получения персональных рекомендаций.", style_normal))
    
    story.append(Spacer(1, 25))
    story.append(PageBreak())
    
    # === ДЕТАЛЬНЫЙ АНАЛИЗ КАЖДОГО ТЕСТА ===
    for test_name, results in sorted(grouped.items()):
        if not results:
            continue
        
        if story and len(story) > 50:
            story.append(PageBreak())
        
        story.append(Paragraph(f"Тест: {test_name}", style_heading))
        
        # Считаем попытки
        test_attempts = 0
        test_successful = 0
        
        for r in results:
            if 'attempt_results' in r:
                attempts = r['attempt_results']
                test_attempts += len(attempts)
                test_successful += sum(1 for a in attempts if isinstance(a, dict) and a.get('correct', False))
            else:
                test_attempts += 1
                if r.get('correct', False):
                    test_successful += 1
        
        accuracy = (test_successful / test_attempts * 100) if test_attempts > 0 else 0
        story.append(Paragraph(f"Попыток: {test_attempts}, Успешных: {test_successful}, Точность: {accuracy:.1f}%", style_small))
        story.append(Spacer(1, 15))
        
        # Рассчитываем метрики
        metrics = calculate_relevant_metrics(results, test_name)
        
        # === БАЗОВЫЕ РЕАКЦИОННЫЕ ТЕСТЫ ===
        if test_name in ['Простая реакция', 'Реакция выбора', 'Сложный выбор']:
            story.append(Paragraph("Анализ базовой реакции", style_subheading))
            
            metrics_data = [["Параметр", "Значение", "Интерпретация"]]
            
            # 1. Время принятия решений
            if 'avg_decision_time' in metrics:
                dt_val = metrics['avg_decision_time']
                if dt_val < 0.2:
                    norm = "Очень быстро (<200 мс)"
                elif dt_val < 0.3:
                    norm = "Быстро (200-300 мс)"
                elif dt_val < 0.4:
                    norm = "Средне (300-400 мс)"
                else:
                    norm = "Медленно (>400 мс)"
                metrics_data.append([
                    Paragraph("Время принятия решений", style_normal),
                    Paragraph(f"{dt_val:.3f} с", style_normal),
                    Paragraph(norm, style_normal)
                ])
            
            # 2. Моторное время
            if 'avg_motor_time' in metrics:
                mt_val = metrics['avg_motor_time']
                if mt_val < 0.1:
                    norm = "Очень быстро (<100 мс)"
                elif mt_val < 0.15:
                    norm = "Быстро (100-150 мс)"
                elif mt_val < 0.2:
                    norm = "Средне (150-200 мс)"
                else:
                    norm = "Медленно (>200 мс)"
                metrics_data.append([
                    Paragraph("Моторное время", style_normal),
                    Paragraph(f"{mt_val:.3f} с", style_normal),
                    Paragraph(norm, style_normal)
                ])
            
            # 3. Общее время реакции
            if 'avg_total_reaction_time' in metrics:
                trt_val = metrics['avg_total_reaction_time']
                metrics_data.append([
                    Paragraph("Общее время реакции", style_normal),
                    Paragraph(f"{trt_val:.3f} с", style_normal),
                    Paragraph(f"Из {test_successful} успешных попыток", style_normal)
                ])
            
            # 4. Пространственная точность
            if 'spatial_accuracy' in metrics:
                sa_val = metrics['spatial_accuracy']
                if sa_val > 90:
                    norm = "Высокая точность (>90%)"
                elif sa_val > 80:
                    norm = "Хорошая точность (80-90%)"
                elif sa_val > 70:
                    norm = "Средняя точность (70-80%)"
                else:
                    norm = "Низкая точность (<70%)"
                metrics_data.append([
                    Paragraph("Пространственная точность", style_normal),
                    Paragraph(f"{sa_val:.1f}%", style_normal),
                    Paragraph(norm, style_normal)
                ])
            
            # 5. Стабильность
            if 'stability' in metrics:
                st_val = metrics['stability']
                if st_val > 80:
                    norm = "Высокая стабильность"
                elif st_val > 60:
                    norm = "Хорошая стабильность"
                elif st_val > 40:
                    norm = "Средняя стабильность"
                else:
                    norm = "Низкая стабильность"
                metrics_data.append([
                    Paragraph("Стабильность реакции", style_normal),
                    Paragraph(f"{st_val:.1f}%", style_normal),
                    Paragraph(norm, style_normal)
                ])
            
            # 6. Ошибки
            if 'total_errors' in metrics and metrics['total_errors'] > 0:
                err_val = metrics['total_errors']
                metrics_data.append([
                    Paragraph("Количество ошибок", style_normal),
                    Paragraph(f"{err_val}", style_normal),
                    Paragraph(f"Из {test_attempts} попыток", style_normal)
                ])
        
        # === ДРУГИЕ ТЕСТЫ ===
        else:
            # Определяем тип теста
            if test_name in ['Реакция на движущийся объект', 'Предвидение траектории', 'Слежение']:
                test_type = "пространственных навыков"
            elif test_name in ['Переключение внимания', 'Тест Струпа']:
                test_type = "когнитивной гибкости"
            elif test_name == 'Оперативная память':
                test_type = "рабочей памяти"
            elif test_name in ['Различение размеров', 'Различение цветов']:
                test_type = "восприятия"
            elif 'Таблицы Горбова-Шульте' in test_name:
                test_type = "зрительного поиска"
            elif test_name in ['Комбинированный A', 'Комбинированный B']:
                test_type = "многозадачности"
            else:
                test_type = "навыков"
            
            story.append(Paragraph(f"Анализ {test_type}", style_subheading))
            
            metrics_data = [["Параметр", "Значение", "Интерпретация"]]
            
            # Общая точность
            if 'accuracy' in metrics:
                acc_val = metrics['accuracy']
                if acc_val > 90:
                    norm = "Отлично (>90%)"
                elif acc_val > 80:
                    norm = "Хорошо (80-90%)"
                elif acc_val > 70:
                    norm = "Средне (70-80%)"
                else:
                    norm = "Требует улучшения (<70%)"
                metrics_data.append([
                    Paragraph("Точность выполнения", style_normal),
                    Paragraph(f"{acc_val:.1f}%", style_normal),
                    Paragraph(norm, style_normal)
                ])
        
        # Создаем таблицу
        if len(metrics_data) > 1:
            col_widths = [2*inch, 1.2*inch, 2.5*inch]
            table = Table(metrics_data, colWidths=col_widths)
            
            # Цвет таблицы
            if test_name in ['Простая реакция', 'Реакция выбора', 'Сложный выбор']:
                table_color = colors.HexColor('#3498DB')
            elif test_name in ['Реакция на движущийся объект', 'Предвидение траектории', 'Слежение']:
                table_color = colors.HexColor('#9B59B6')
            elif test_name in ['Переключение внимания', 'Тест Струпа']:
                table_color = colors.HexColor('#2ECC71')
            elif test_name == 'Оперативная память':
                table_color = colors.HexColor('#1ABC9C')
            elif test_name in ['Различение размеров', 'Различение цветов']:
                table_color = colors.HexColor('#E67E22')
            elif test_name in ['Комбинированный A', 'Комбинированный B']:
                table_color = colors.HexColor('#E74C3C')
            else:
                table_color = colors.HexColor('#7F8C8D')
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), table_color),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,-1), normal_font),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9F9')]),
                ('ALIGN', (1,0), (1,-1), 'CENTER'),
                ('PADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            
            story.append(table)
            
            # Выводы
            story.append(Spacer(1, 10))
            story.append(Paragraph("Ключевые выводы:", style_normal))
            
            conclusions = generate_test_conclusions(test_name, metrics, test_attempts, test_successful)
            for conclusion in conclusions:
                story.append(Paragraph(f"• {conclusion}", style_normal))
        
        story.append(Spacer(1, 20))
    
    try:
        doc.build(story)
        print(f"Отчёт успешно сохранён: {output_path}")
        return True
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_test_conclusions(test_name, metrics, total_attempts, successful_attempts):
    """Генерация выводов для конкретного теста"""
    conclusions = []
    
    accuracy = metrics.get('accuracy', 0)
    
    # Базовые реакционные тесты
    if test_name in ['Простая реакция', 'Реакция выбора', 'Сложный выбор']:
        # Точность
        if accuracy > 90:
            conclusions.append(f"Отличная точность реакции ({accuracy:.1f}%).")
        elif accuracy > 70:
            conclusions.append(f"Хорошая точность реакции ({accuracy:.1f}%).")
        else:
            conclusions.append(f"Требуется улучшение точности ({accuracy:.1f}%).")
        
        # Время принятия решений
        if 'avg_decision_time' in metrics:
            dt_val = metrics['avg_decision_time']
            if dt_val < 0.25:
                conclusions.append("Быстрое принятие решений.")
            elif dt_val < 0.35:
                conclusions.append("Средняя скорость принятия решений.")
            else:
                conclusions.append("Медленное принятие решений, требуется тренировка.")
        
        # Пространственная точность
        if 'spatial_accuracy' in metrics:
            sa_val = metrics['spatial_accuracy']
            if sa_val < 80:
                conclusions.append("Требуется улучшение точности попадания.")
        
        # Стабильность
        if 'stability' in metrics:
            st_val = metrics['stability']
            if st_val < 60:
                conclusions.append("Нестабильная работа, требуется тренировка стабильности.")
        
        # Ошибки
        if 'total_errors' in metrics and metrics['total_errors'] > 0:
            err_val = metrics['total_errors']
            conclusions.append(f"{err_val} ошибок из {total_attempts} попыток.")
    
    # Общий вывод
    if not conclusions:
        if successful_attempts > 0:
            conclusions.append(f"Выполнено {successful_attempts} успешных попыток из {total_attempts}.")
        else:
            conclusions.append("Для подробного анализа выполните больше успешных попыток этого теста.")
    
    return conclusions[:3]
