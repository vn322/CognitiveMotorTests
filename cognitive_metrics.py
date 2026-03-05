# cognitive_metrics.py (исправленная версия)
import math
from collections import defaultdict
import statistics

class CognitiveMotorAnalyzer:
    """Анализатор когнитивно-моторной подготовленности"""
    
    @staticmethod
    def analyze_comprehensive_performance(all_results):
        """Комплексный анализ результатов всех тестов"""
        analysis = {
            'basic_reaction': {},
            'spatial_skills': {},
            'cognitive_flexibility': {},
            'perceptual_skills': {},
            'working_memory': {},
            'combined_performance': {},
            'overall_score': 0,
            'recommendations': []
        }
        
        # Группируем результаты по тестам
        grouped = defaultdict(list)
        for r in all_results:
            if isinstance(r, dict):
                test_name = r.get('test_name', '')
                grouped[test_name].append(r)
        
        # 1. Базовые реактивные способности
        basic_tests = ['Простая реакция', 'Реакция выбора', 'Сложный выбор']
        analysis['basic_reaction'] = CognitiveMotorAnalyzer._analyze_basic_reaction(
            grouped, basic_tests
        )
        
        # 2. Пространственные навыки
        spatial_tests = ['Реакция на движущийся объект', 'Слежение', 'Предвидение траектории']
        analysis['spatial_skills'] = CognitiveMotorAnalyzer._analyze_spatial_skills(
            grouped, spatial_tests
        )
        
        # 3. Когнитивная гибкость
        cognitive_tests = ['Переключение внимания', 'Тест Струпа', 'Таблицы Горбова-Шульте (с подсказкой)', 
                          'Таблицы Горбова-Шульте (без подсказки)']
        analysis['cognitive_flexibility'] = CognitiveMotorAnalyzer._analyze_cognitive_flexibility(
            grouped, cognitive_tests
        )
        
        # 4. Перцептивные навыки (восприятие)
        perceptual_tests = ['Различение размеров', 'Различение цветов']
        analysis['perceptual_skills'] = CognitiveMotorAnalyzer._analyze_perceptual_skills(
            grouped, perceptual_tests
        )
        
        # 5. Рабочая память
        memory_tests = ['Оперативная память', 'Таблицы Горбова-Шульте (без подсказки)']
        analysis['working_memory'] = CognitiveMotorAnalyzer._analyze_working_memory(
            grouped, memory_tests
        )
        
        # 6. Комбинированные тесты
        combined_tests = ['Комбинированный A', 'Комбинированный B']
        analysis['combined_performance'] = CognitiveMotorAnalyzer._analyze_combined_tests(
            grouped, combined_tests
        )
        
        # 7. Общий балл
        analysis['overall_score'] = CognitiveMotorAnalyzer._calculate_overall_score(analysis)
        
        # 8. Рекомендации
        analysis['recommendations'] = CognitiveMotorAnalyzer._generate_recommendations(analysis)
        
        return analysis
    
    @staticmethod
    def _analyze_basic_reaction(grouped, test_names):
        """Анализ базовых реакций"""
        metrics = {
            'score': 0,
            'avg_decision_time': 0,
            'avg_motor_time': 0,
            'avg_accuracy': 0,
            'consistency': 0,
            'interpretation': ''
        }
        
        decision_times = []
        motor_times = []
        accuracies = []
        reaction_times = []
        
        for test_name in test_names:
            if test_name in grouped and grouped[test_name]:
                results = grouped[test_name]
                for r in results:
                    latency = r.get('latency')
                    if latency and latency > 0:
                        decision_times.append(latency)
                    
                    motor_time = r.get('motor_time')
                    if motor_time:
                        motor_times.append(motor_time)
                    
                    total_rt = r.get('total_rt')
                    if total_rt:
                        reaction_times.append(total_rt)
                    
                    if r.get('correct', False):
                        accuracies.append(1)
                    else:
                        accuracies.append(0)
        
        if decision_times:
            metrics['avg_decision_time'] = statistics.mean(decision_times)
            metrics['decision_time_std'] = statistics.stdev(decision_times) if len(decision_times) > 1 else 0
        if motor_times:
            metrics['avg_motor_time'] = statistics.mean(motor_times)
        if accuracies:
            metrics['avg_accuracy'] = sum(accuracies) / len(accuracies) * 100
        if reaction_times:
            cv = statistics.stdev(reaction_times) / statistics.mean(reaction_times) if statistics.mean(reaction_times) > 0 else 0
            metrics['consistency'] = max(0, 100 - (cv * 100))
        
        # Оценка
        reaction_score = 0
        if metrics['avg_decision_time'] < 0.3:
            reaction_score += 40
        elif metrics['avg_decision_time'] < 0.5:
            reaction_score += 30
        elif metrics['avg_decision_time'] < 0.7:
            reaction_score += 20
        else:
            reaction_score += 10
        
        if metrics['avg_accuracy'] > 90:
            reaction_score += 40
        elif metrics['avg_accuracy'] > 70:
            reaction_score += 30
        elif metrics['avg_accuracy'] > 50:
            reaction_score += 20
        else:
            reaction_score += 10
        
        if metrics['consistency'] > 80:
            reaction_score += 20
        elif metrics['consistency'] > 60:
            reaction_score += 15
        elif metrics['consistency'] > 40:
            reaction_score += 10
        else:
            reaction_score += 5
        
        metrics['score'] = min(100, reaction_score)
        
        # Интерпретация
        if metrics['score'] >= 80:
            metrics['interpretation'] = 'Отличные реактивные способности'
        elif metrics['score'] >= 60:
            metrics['interpretation'] = 'Хорошие реактивные способности'
        elif metrics['score'] >= 40:
            metrics['interpretation'] = 'Средние реактивные способности'
        else:
            metrics['interpretation'] = 'Требуется тренировка реакции'
        
        return metrics
    
    @staticmethod
    def _analyze_spatial_skills(grouped, test_names):
        """Анализ пространственных навыков"""
        metrics = {
            'score': 0,
            'temporal_accuracy': 0,
            'spatial_accuracy': 0,
            'prediction_accuracy': 0,
            'interpretation': ''
        }
        
        timing_errors = []
        distances = []
        prediction_accuracies = []
        
        if 'Реакция на движущийся объект' in grouped:
            for r in grouped['Реакция на движущийся объект']:
                timing_delay = r.get('timing_delay')
                if timing_delay is not None:
                    timing_errors.append(abs(timing_delay))
                
                distance = r.get('distance_from_center')
                if distance:
                    distances.append(distance)
        
        if 'Предвидение траектории' in grouped:
            for r in grouped['Предвидение траектории']:
                accuracy = r.get('prediction_accuracy', 0)
                prediction_accuracies.append(accuracy)
        
        if timing_errors:
            metrics['temporal_accuracy'] = 100 - (statistics.mean(timing_errors) * 100)
        if distances:
            avg_distance = statistics.mean(distances)
            metrics['spatial_accuracy'] = max(0, 100 - (avg_distance / 10))
        if prediction_accuracies:
            metrics['prediction_accuracy'] = statistics.mean(prediction_accuracies)
        
        spatial_score = 0
        if metrics['temporal_accuracy'] > 90:
            spatial_score += 40
        elif metrics['temporal_accuracy'] > 70:
            spatial_score += 30
        elif metrics['temporal_accuracy'] > 50:
            spatial_score += 20
        else:
            spatial_score += 10
        
        if metrics['spatial_accuracy'] > 90:
            spatial_score += 40
        elif metrics['spatial_accuracy'] > 70:
            spatial_score += 30
        elif metrics['spatial_accuracy'] > 50:
            spatial_score += 20
        else:
            spatial_score += 10
        
        if metrics['prediction_accuracy'] > 70:
            spatial_score += 20
        elif metrics['prediction_accuracy'] > 50:
            spatial_score += 15
        elif metrics['prediction_accuracy'] > 30:
            spatial_score += 10
        else:
            spatial_score += 5
        
        metrics['score'] = min(100, spatial_score)
        
        if metrics['score'] >= 80:
            metrics['interpretation'] = 'Отличные пространственные способности'
        elif metrics['score'] >= 60:
            metrics['interpretation'] = 'Хорошие пространственные способности'
        elif metrics['score'] >= 40:
            metrics['interpretation'] = 'Средние пространственные способности'
        else:
            metrics['interpretation'] = 'Требуется тренировка пространственного мышления'
        
        return metrics
    
    @staticmethod
    def _analyze_cognitive_flexibility(grouped, test_names):
        """Анализ когнитивной гибкости"""
        metrics = {
            'score': 0,
            'switch_cost': 0,
            'stroop_effect': 0,
            'attention_accuracy': 0,
            'interpretation': ''
        }
        
        if 'Переключение внимания' in grouped and grouped['Переключение внимания']:
            for r in grouped['Переключение внимания']:
                switch_cost = r.get('switch_cost', 0)
                if switch_cost:
                    metrics['switch_cost'] = abs(switch_cost)
                
                accuracy = r.get('accuracy', 0)
                if accuracy:
                    metrics['attention_accuracy'] = accuracy
        
        if 'Тест Струпа' in grouped and grouped['Тест Струпа']:
            stroop_effects = []
            for r in grouped['Тест Струпа']:
                stroop_effect = r.get('stroop_effect')
                if stroop_effect:
                    stroop_effects.append(stroop_effect)
            if stroop_effects:
                metrics['stroop_effect'] = statistics.mean(stroop_effects)
        
        cognitive_score = 0
        
        if metrics['switch_cost'] < 0.1:
            cognitive_score += 40
        elif metrics['switch_cost'] < 0.2:
            cognitive_score += 30
        elif metrics['switch_cost'] < 0.3:
            cognitive_score += 20
        else:
            cognitive_score += 10
        
        if metrics['stroop_effect'] < 0.1:
            cognitive_score += 30
        elif metrics['stroop_effect'] < 0.2:
            cognitive_score += 25
        elif metrics['stroop_effect'] < 0.3:
            cognitive_score += 20
        else:
            cognitive_score += 10
        
        if metrics['attention_accuracy'] > 90:
            cognitive_score += 30
        elif metrics['attention_accuracy'] > 70:
            cognitive_score += 25
        elif metrics['attention_accuracy'] > 50:
            cognitive_score += 20
        else:
            cognitive_score += 10
        
        metrics['score'] = min(100, cognitive_score)
        
        if metrics['score'] >= 80:
            metrics['interpretation'] = 'Отличная когнитивная гибкость'
        elif metrics['score'] >= 60:
            metrics['interpretation'] = 'Хорошая когнитивная гибкость'
        elif metrics['score'] >= 40:
            metrics['interpretation'] = 'Средняя когнитивная гибкость'
        else:
            metrics['interpretation'] = 'Требуется тренировка когнитивной гибкости'
        
        return metrics
    
    @staticmethod
    def _analyze_perceptual_skills(grouped, test_names):
        """Анализ перцептивных навыков (восприятия)"""
        metrics = {
            'score': 0,
            'size_discrimination_accuracy': 0,
            'color_discrimination_accuracy': 0,
            'size_bias_score': 50,  # 50 = нейтрально
            'color_bias_score': 50,  # 50 = нейтрально
            'perceptual_speed': 0,
            'size_bias_interpretation': '',
            'color_bias_interpretation': '',
            'interpretation': ''
        }
        
        size_accuracies = []
        color_accuracies = []
        perceptual_times = []
        size_errors = []
        color_errors = []
        
        # Анализ теста на различение размеров
        if 'Различение размеров' in grouped and grouped['Различение размеров']:
            for r in grouped['Различение размеров']:
                if r.get('correct', False):
                    size_accuracies.append(1)
                else:
                    size_accuracies.append(0)
                
                rt = r.get('total_rt')
                if rt:
                    perceptual_times.append(rt)
                
                # Анализ склонности к преувеличению/преуменьшению
                size_error = r.get('avg_size_error', 0)
                size_errors.append(size_error)
                
                all_errors = r.get('all_errors', [])
                if all_errors:
                    # Рассчитываем распределение ошибок
                    positive_errors = sum(1 for e in all_errors if e > 0)
                    negative_errors = sum(1 for e in all_errors if e < 0)
                    total_errors = len(all_errors)
                    
                    if total_errors > 0:
                        if positive_errors > negative_errors * 1.5:
                            metrics['size_bias_score'] = 70  # Склонность к преувеличению
                            metrics['size_bias_interpretation'] = 'Склонность к преувеличению размеров'
                        elif negative_errors > positive_errors * 1.5:
                            metrics['size_bias_score'] = 30  # Склонность к преуменьшению
                            metrics['size_bias_interpretation'] = 'Склонность к преуменьшению размеров'
                        else:
                            metrics['size_bias_score'] = 50  # Нейтрально
                            metrics['size_bias_interpretation'] = 'Нейтральное восприятие размеров'
        
        # Анализ теста на различение цветов
        if 'Различение цветов' in grouped and grouped['Различение цветов']:
            for r in grouped['Различение цветов']:
                if r.get('correct', False):
                    color_accuracies.append(1)
                else:
                    color_accuracies.append(0)
                
                rt = r.get('total_rt')
                if rt:
                    perceptual_times.append(rt)
        
        # Рассчитываем метрики
        if size_accuracies:
            metrics['size_discrimination_accuracy'] = sum(size_accuracies) / len(size_accuracies) * 100
        
        if color_accuracies:
            metrics['color_discrimination_accuracy'] = sum(color_accuracies) / len(color_accuracies) * 100
        
        if perceptual_times:
            avg_time = statistics.mean(perceptual_times)
            if avg_time < 0.8:
                metrics['perceptual_speed'] = 90
            elif avg_time < 1.2:
                metrics['perceptual_speed'] = 70
            elif avg_time < 1.8:
                metrics['perceptual_speed'] = 50
            else:
                metrics['perceptual_speed'] = 30
        
        # Общая оценка перцептивных навыков
        # Учитываем точность, скорость и отсутствие систематических ошибок
        perceptual_score = (
            metrics['size_discrimination_accuracy'] * 0.25 +
            metrics['color_discrimination_accuracy'] * 0.25 +
            metrics['perceptual_speed'] * 0.20 +
            (100 - abs(metrics['size_bias_score'] - 50) * 2) * 0.15 +  # Штраф за систематические ошибки
            (100 - abs(metrics['color_bias_score'] - 50) * 2) * 0.15
        )
        metrics['score'] = min(100, perceptual_score)
        
        # Собираем детализированную интерпретацию
        interpretations = []
        
        if metrics['size_discrimination_accuracy'] > 80:
            interpretations.append("отличное различение размеров")
        elif metrics['size_discrimination_accuracy'] > 60:
            interpretations.append("хорошее различение размеров")
        else:
            interpretations.append("требуется улучшение в различении размеров")
        
        if metrics['color_discrimination_accuracy'] > 80:
            interpretations.append("отличное цветовосприятие")
        elif metrics['color_discrimination_accuracy'] > 60:
            interpretations.append("хорошее цветовосприятие")
        else:
            interpretations.append("требуется улучшение в различении цветов")
        
        if metrics['size_bias_interpretation']:
            interpretations.append(metrics['size_bias_interpretation'].lower())
        
        metrics['interpretation'] = '; '.join(interpretations).capitalize()
        
        return metrics
    
    @staticmethod
    def _analyze_working_memory(grouped, test_names):
        """Анализ рабочей памяти"""
        metrics = {
            'score': 0,
            'memory_capacity': 0,
            'memory_speed': 0,
            'search_efficiency': 0,
            'interpretation': ''
        }
        
        memory_accuracies = []
        memory_times = []
        search_times = []
        
        if 'Оперативная память' in grouped and grouped['Оперативная память']:
            for r in grouped['Оперативная память']:
                capacity = r.get('memory_capacity', 0)
                if capacity:
                    metrics['memory_capacity'] = capacity
                
                accuracy = r.get('accuracy', 0)
                if accuracy:
                    memory_accuracies.append(accuracy)
                
                rt = r.get('avg_response_time')
                if rt:
                    memory_times.append(rt)
        
        if 'Таблицы Горбова-Шульте (без подсказки)' in grouped and grouped['Таблицы Горбова-Шульте (без подсказки)']:
            for r in grouped['Таблицы Горбова-Шульте (без подсказки)']:
                search_time = r.get('avg_search_time')
                if search_time:
                    search_times.append(search_time)
        
        if memory_accuracies:
            metrics['memory_capacity'] = statistics.mean(memory_accuracies) * 100
        
        if memory_times:
            avg_memory_time = statistics.mean(memory_times)
            if avg_memory_time < 1.5:
                metrics['memory_speed'] = 90
            elif avg_memory_time < 2.5:
                metrics['memory_speed'] = 70
            elif avg_memory_time < 3.5:
                metrics['memory_speed'] = 50
            else:
                metrics['memory_speed'] = 30
        
        if search_times:
            avg_search_time = statistics.mean(search_times)
            if avg_search_time < 2.0:
                metrics['search_efficiency'] = 90
            elif avg_search_time < 3.0:
                metrics['search_efficiency'] = 70
            elif avg_search_time < 4.0:
                metrics['search_efficiency'] = 50
            else:
                metrics['search_efficiency'] = 30
        
        memory_score = (
            metrics['memory_capacity'] * 0.5 +
            metrics['memory_speed'] * 0.3 +
            metrics['search_efficiency'] * 0.2
        )
        metrics['score'] = min(100, memory_score)
        
        if metrics['score'] >= 80:
            metrics['interpretation'] = 'Отличная рабочая память'
        elif metrics['score'] >= 60:
            metrics['interpretation'] = 'Хорошая рабочая память'
        elif metrics['score'] >= 40:
            metrics['interpretation'] = 'Средняя рабочая память'
        else:
            metrics['interpretation'] = 'Требуется тренировка рабочей памяти'
        
        return metrics
    
    @staticmethod
    def _analyze_combined_tests(grouped, test_names):
        """Анализ комбинированных тестов"""
        metrics = {
            'score': 0,
            'multi_task_efficiency': 0,
            'dynamic_adaptation': 0,
            'interpretation': ''
        }
        
        combined_accuracies = []
        reaction_times = []
        
        for test_name in test_names:
            if test_name in grouped and grouped[test_name]:
                results = grouped[test_name]
                for r in results:
                    if r.get('correct', False):
                        combined_accuracies.append(1)
                    else:
                        combined_accuracies.append(0)
                    
                    rt = r.get('total_rt')
                    if rt:
                        reaction_times.append(rt)
        
        if combined_accuracies:
            metrics['multi_task_efficiency'] = sum(combined_accuracies) / len(combined_accuracies) * 100
        
        if reaction_times:
            avg_rt = statistics.mean(reaction_times)
            if avg_rt < 1.5:
                metrics['dynamic_adaptation'] = 90
            elif avg_rt < 2.0:
                metrics['dynamic_adaptation'] = 70
            elif avg_rt < 2.5:
                metrics['dynamic_adaptation'] = 50
            else:
                metrics['dynamic_adaptation'] = 30
        
        combined_score = (metrics['multi_task_efficiency'] * 0.6 + 
                         metrics['dynamic_adaptation'] * 0.4)
        metrics['score'] = combined_score
        
        if metrics['score'] >= 80:
            metrics['interpretation'] = 'Отличные навыки многозадачности'
        elif metrics['score'] >= 60:
            metrics['interpretation'] = 'Хорошие навыки многозадачности'
        elif metrics['score'] >= 40:
            metrics['interpretation'] = 'Средние навыки многозадачности'
        else:
            metrics['interpretation'] = 'Требуется тренировка многозадачности'
        
        return metrics
    
    @staticmethod
    def _calculate_overall_score(analysis):
        """Расчет общего балла"""
        weights = {
            'basic_reaction': 0.20,
            'spatial_skills': 0.20,
            'cognitive_flexibility': 0.20,
            'perceptual_skills': 0.15,
            'working_memory': 0.15,
            'combined_performance': 0.10
        }
        
        overall_score = 0
        for category, weight in weights.items():
            if category in analysis and 'score' in analysis[category]:
                overall_score += analysis[category]['score'] * weight
        
        return min(100, overall_score)
    
    @staticmethod
    def _generate_recommendations(analysis):
        """Генерация рекомендаций на основе анализа"""
        recommendations = []
        
        # Рекомендации по базовым реакциям
        if analysis['basic_reaction']['score'] < 60:
            recommendations.append(
                "Тренируйте простые реакции: выполните 10-15 попыток теста 'Простая реакция' ежедневно"
            )
        
        # Рекомендации по пространственным навыкам
        if analysis['spatial_skills']['score'] < 60:
            recommendations.append(
                "Улучшайте пространственное мышление: уделите внимание тестам 'Реакция на движущийся объект' и 'Предвидение траектории'"
            )
        
        # Рекомендации по когнитивной гибкости
        if analysis['cognitive_flexibility']['score'] < 60:
            recommendations.append(
                "Развивайте когнитивную гибкость: регулярно выполняйте тест 'Переключение внимания' и 'Тест Струпа'"
            )
        
        # Рекомендации по перцептивным навыкам
        if 'perceptual_skills' in analysis and analysis['perceptual_skills']['score'] < 60:
            # Детализированные рекомендации по восприятию
            perceptual = analysis['perceptual_skills']
            
            if perceptual.get('size_discrimination_accuracy', 0) < 60:
                recommendations.append(
                    "Улучшайте восприятие размеров: практикуйте тест 'Различение размеров', фокусируясь на точности, а не скорости"
                )
            
            if perceptual.get('color_discrimination_accuracy', 0) < 60:
                recommendations.append(
                    "Улучшайте цветовосприятие: практикуйте тест 'Различение цветов' для развития цветовой чувствительности"
                )
            
            # Рекомендации по систематическим ошибкам
            if perceptual.get('size_bias_score', 50) > 65:
                recommendations.append(
                    "Обратите внимание на склонность к преувеличению размеров. Старайтесь объективно оценивать размеры объектов"
                )
            elif perceptual.get('size_bias_score', 50) < 35:
                recommendations.append(
                    "Обратите внимание на склонность к преуменьшению размеров. Старайтесь объективно оценивать размеры объектов"
                )
        
        # Рекомендации по рабочей памяти
        if 'working_memory' in analysis and analysis['working_memory']['score'] < 60:
            recommendations.append(
                "Тренируйте рабочую память: выполняйте тест 'Оперативная память' и 'Таблицы Горбова-Шульте'"
            )
        
        # Рекомендации по комбинированным тестам
        if analysis['combined_performance']['score'] < 60:
            recommendations.append(
                "Тренируйте многозадачность: практикуйте комбинированные тесты для улучшения распределения внимания"
            )
        
        # Общие рекомендации
        if analysis['overall_score'] >= 80:
            recommendations.append(
                "Отличные результаты! Поддерживайте текущий уровень регулярными тренировками 2-3 раза в неделю"
            )
        elif analysis['overall_score'] >= 60:
            recommendations.append(
                "Хорошие показатели. Для улучшения результатов сосредоточьтесь на слабых областях"
            )
        else:
            recommendations.append(
                "Рекомендуется систематическая тренировка 3-4 раза в неделю по 20-30 минут"
            )
        
        return recommendations