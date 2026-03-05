# progress_tracker.py
import json
import os
from datetime import datetime

class ProgressTracker:
    def __init__(self, data_file='progress_data.json'):
        self.data_file = data_file
        self.progress_data = self.load_data()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'sessions': []}
    
    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
    
    def add_session(self, analysis_results, session_date=None):
        if session_date is None:
            session_date = datetime.now().isoformat()
        
        session_data = {
            'date': session_date,
            'overall_score': analysis_results.get('overall_score', 0),
            'category_scores': {
                'basic_reaction': analysis_results.get('basic_reaction', {}).get('score', 0),
                'spatial_skills': analysis_results.get('spatial_skills', {}).get('score', 0),
                'cognitive_flexibility': analysis_results.get('cognitive_flexibility', {}).get('score', 0),
                'combined_performance': analysis_results.get('combined_performance', {}).get('score', 0)
            },
            'recommendations': analysis_results.get('recommendations', [])
        }
        
        self.progress_data['sessions'].append(session_data)
        self.save_data()
    
    def get_progress_summary(self):
        if not self.progress_data['sessions']:
            return None
        
        sessions = self.progress_data['sessions']
        first_score = sessions[0]['overall_score']
        last_score = sessions[-1]['overall_score']
        
        return {
            'total_sessions': len(sessions),
            'first_score': first_score,
            'last_score': last_score,
            'improvement': last_score - first_score,
            'avg_score': sum(s['overall_score'] for s in sessions) / len(sessions)
        }