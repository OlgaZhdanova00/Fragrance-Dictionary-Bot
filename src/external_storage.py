"""
Модуль для сохранения важных данных во внешних сервисах
"""
import json
import os
from datetime import datetime
from typing import Dict, List

class ExternalStorage:
    """Класс для сохранения данных во внешних сервисах"""
    
    def __init__(self):
        self.log_file = "data/user_data.json"
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """Создает файл для логирования если его нет"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump({"searches": [], "suggestions": []}, f, ensure_ascii=False, indent=2)
    
    def log_search(self, user_id: int, query: str, found: bool = False):
        """Логирует поисковый запрос"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            search_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "query": query,
                "found": found
            }
            
            data["searches"].append(search_entry)
            
            # Оставляем только последние 1000 записей
            if len(data["searches"]) > 1000:
                data["searches"] = data["searches"][-1000:]
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка логирования поиска: {e}")
    
    def save_user_suggestion(self, user_id: int, username: str, term: str, definition: str):
        """Сохраняет предложение пользователя"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            suggestion_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "username": username,
                "term": term,
                "definition": definition,
                "status": "pending"
            }
            
            data["suggestions"].append(suggestion_entry)
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения предложения: {e}")
            return False
    
    def get_suggestions_count(self) -> int:
        """Получает количество предложений"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return len([s for s in data["suggestions"] if s.get("status") == "pending"])
        except:
            return 0
    
    def get_searches_count(self) -> int:
        """Получает количество поисков"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return len(data["searches"])
        except:
            return 0
