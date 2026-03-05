# metrics.py (дополнение)
def calculate_timing_accuracy(timing_errors):
    """Рассчитать точность временной реакции"""
    if not timing_errors:
        return 0.0
    
    # Среднеквадратичная ошибка
    mse = sum(e*e for e in timing_errors) / len(timing_errors)
    
    # Коэффициент точности (чем ближе к 0, тем лучше)
    accuracy = 1.0 / (1.0 + mse) if mse > 0 else 1.0
    
    return accuracy * 100  # В процентах

def analyze_trajectory_performance(results_by_trajectory):
    """Анализ производительности по разным траекториям"""
    analysis = {}
    
    for traj_type, results in results_by_trajectory.items():
        if not results:
            continue
            
        avg_error = sum(r.get('timing_delay', 0) for r in results) / len(results)
        avg_distance = sum(r.get('distance_from_center', 0) for r in results) / len(results)
        accuracy = sum(1 for r in results if r['correct']) / len(results) * 100
        
        analysis[traj_type] = {
            'avg_error': avg_error,
            'avg_distance': avg_distance,
            'accuracy': accuracy,
            'count': len(results)
        }
    
    return analysis

def calculate_reaction_consistency(reaction_times):
    """Рассчитать консистентность времени реакции"""
    if len(reaction_times) < 2:
        return 0.0
    
    mean = sum(reaction_times) / len(reaction_times)
    variance = sum((rt - mean) ** 2 for rt in reaction_times) / len(reaction_times)
    
    # Коэффициент вариации (ниже = более стабильно)
    cv = (math.sqrt(variance) / mean) if mean > 0 else 0
    
    # Конвертируем в оценку стабильности (0-100%)
    stability = max(0, 100 - (cv * 100))
    
    return stability