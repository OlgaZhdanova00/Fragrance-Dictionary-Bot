"""
Модуль для работы с базой данных SQLite
Содержит все функции для управления парфюмерными терминами
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH

class PerfumeDatabase:
    def __init__(self, db_path: str = None):
        """Инициализация базы данных"""
        self.db_path = db_path or DATABASE_PATH
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Создает папку для базы данных если её нет"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Получает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Для удобного доступа к колонкам
        return conn
    
    def init_database(self):
        """Создает таблицы если их нет"""
        with self.get_connection() as conn:
            # Таблица категорий
            conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица терминов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT UNIQUE NOT NULL,
                    definition TEXT NOT NULL,
                    category_id INTEGER,
                    examples TEXT,
                    synonyms TEXT,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            # Таблица статистики поиска
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    term_id INTEGER,
                    query TEXT NOT NULL,
                    found BOOLEAN DEFAULT 0,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (term_id) REFERENCES terms (id)
                )
            ''')
            
            # Таблица предложений от пользователей
            conn.execute('''
                CREATE TABLE IF NOT EXISTS term_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    suggested_term TEXT NOT NULL,
                    suggested_definition TEXT NOT NULL,
                    suggested_category TEXT,
                    suggested_examples TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def add_category(self, name: str, description: str = None) -> int:
        """Добавляет новую категорию"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'INSERT INTO categories (name, description) VALUES (?, ?)',
                (name, description)
            )
            return cursor.lastrowid
    
    def get_categories(self) -> List[Dict]:
        """Получает все категории"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM categories ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def add_term(self, term: str, definition: str, category_name: str = None, 
                 examples: str = None, synonyms: str = None) -> int:
        """Добавляет новый термин"""
        with self.get_connection() as conn:
            category_id = None
            if category_name:
                # Ищем категорию или создаем новую
                cursor = conn.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
                result = cursor.fetchone()
                if result:
                    category_id = result['id']
                else:
                    category_id = self.add_category(category_name)
            
            cursor = conn.execute('''
                INSERT INTO terms (term, definition, category_id, examples, synonyms)
                VALUES (?, ?, ?, ?, ?)
            ''', (term, definition, category_id, examples, synonyms))
            
            return cursor.lastrowid
    
    def search_terms(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск терминов с разными стратегиями"""
        query_lower = query.lower().strip()
        results = []
        
        with self.get_connection() as conn:
            # Получаем все термины для поиска в Python (SQLite плохо работает с русскими буквами)
            cursor = conn.execute('''
                SELECT t.*, c.name as category_name 
                FROM terms t 
                LEFT JOIN categories c ON t.category_id = c.id 
                ORDER BY t.usage_count DESC, t.term
            ''')
            all_terms = [dict(row) for row in cursor.fetchall()]
            
            # 1. Точное совпадение
            for term_data in all_terms:
                if term_data['term'].lower() == query_lower:
                    return [term_data]
            
            # 2. Поиск по синонимам
            synonym_results = []
            for term_data in all_terms:
                if term_data['synonyms'] and query_lower in term_data['synonyms'].lower():
                    synonym_results.append(term_data)
            if synonym_results:
                return synonym_results[:limit]
            
            # 3. Частичное совпадение в названии
            partial_results = []
            for term_data in all_terms:
                if query_lower in term_data['term'].lower():
                    partial_results.append(term_data)
            if partial_results:
                return partial_results[:limit]
            
            # 4. Поиск в определениях
            definition_results = []
            for term_data in all_terms:
                if query_lower in term_data['definition'].lower():
                    definition_results.append(term_data)
            
            return definition_results[:limit]
    
    def get_term_by_id(self, term_id: int) -> Optional[Dict]:
        """Получает термин по ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT t.*, c.name as category_name 
                FROM terms t 
                LEFT JOIN categories c ON t.category_id = c.id 
                WHERE t.id = ?
            ''', (term_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_random_term(self) -> Optional[Dict]:
        """Получает случайный термин"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT t.*, c.name as category_name 
                FROM terms t 
                LEFT JOIN categories c ON t.category_id = c.id 
                ORDER BY RANDOM() 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def increment_usage(self, term_id: int):
        """Увеличивает счетчик использования термина"""
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE terms SET usage_count = usage_count + 1 WHERE id = ?',
                (term_id,)
            )
    
    def log_search(self, user_id: int, query: str, term_id: int = None, found: bool = False):
        """Логирует поисковый запрос"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO search_stats (user_id, term_id, query, found)
                VALUES (?, ?, ?, ?)
            ''', (user_id, term_id, query, found))
    
    def add_suggestion(self, user_id: int, username: str, term: str, definition: str,
                      category: str = None, examples: str = None) -> int:
        """Добавляет предложение нового термина от пользователя"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO term_suggestions 
                (user_id, username, suggested_term, suggested_definition, 
                 suggested_category, suggested_examples)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, term, definition, category, examples))
            return cursor.lastrowid
    
    def get_pending_suggestions(self) -> List[Dict]:
        """Получает все ожидающие модерации предложения"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM term_suggestions 
                WHERE status = 'pending' 
                ORDER BY created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Получает статистику базы данных"""
        with self.get_connection() as conn:
            # Общая статистика
            stats = {}
            
            # Количество терминов
            cursor = conn.execute('SELECT COUNT(*) as count FROM terms')
            stats['total_terms'] = cursor.fetchone()['count']
            
            # Количество категорий
            cursor = conn.execute('SELECT COUNT(*) as count FROM categories')
            stats['total_categories'] = cursor.fetchone()['count']
            
            # Топ-5 популярных терминов
            cursor = conn.execute('''
                SELECT term, usage_count 
                FROM terms 
                WHERE usage_count > 0 
                ORDER BY usage_count DESC 
                LIMIT 5
            ''')
            stats['popular_terms'] = [dict(row) for row in cursor.fetchall()]
            
            # Количество поисков за последние 7 дней
            cursor = conn.execute('''
                SELECT COUNT(*) as count 
                FROM search_stats 
                WHERE search_date > datetime('now', '-7 days')
            ''')
            stats['searches_week'] = cursor.fetchone()['count']
            
            # Ожидающие предложения
            cursor = conn.execute('SELECT COUNT(*) as count FROM term_suggestions WHERE status = "pending"')
            stats['pending_suggestions'] = cursor.fetchone()['count']
            
            return stats
    
    def backup_database(self, backup_path: str = None) -> str:
        """Создает резервную копию базы данных"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backups/backup_{timestamp}.db"
        
        # Создаем папку для бэкапов
        backup_dir = os.path.dirname(backup_path)
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        # Копируем базу данных
        import shutil
        shutil.copy2(self.db_path, backup_path)
        return backup_path

# Функция для инициализации базы данных с начальными данными
def populate_initial_data(db: PerfumeDatabase):
    """Заполняет базу данных начальными терминами"""
    
    # Проверяем, есть ли уже данные
    with db.get_connection() as conn:
        cursor = conn.execute('SELECT COUNT(*) as count FROM terms')
        if cursor.fetchone()['count'] > 0:
            print("База данных уже содержит термины, пропускаем инициализацию")
            return
    
    print("Заполняем базу данных начальными терминами...")
    
    # Начальные категории и термины
    initial_data = [
        # Структура аромата
        {
            "category": "Структура аромата",
            "terms": [
                {
                    "term": "Верхние ноты",
                    "definition": "Ароматы, которые ощущаются сразу после нанесения парфюма и испаряются в течение первых 15-30 минут",
                    "examples": "Цитрус, мята, эвкалипт, альдегиды",
                    "synonyms": "топ ноты, head notes"
                },
                {
                    "term": "Средние ноты",
                    "definition": "Сердце аромата, которое раскрывается через 15-30 минут после нанесения и держится 2-4 часа",
                    "examples": "Роза, жасмин, герань, специи",
                    "synonyms": "ноты сердца, heart notes"
                },
                {
                    "term": "Базовые ноты",
                    "definition": "Финальная часть аромата, самая стойкая, может держаться на коже до 24 часов",
                    "examples": "Сандал, мускус, амбра, ваниль",
                    "synonyms": "база, base notes"
                }
            ]
        },
        
        # Жаргон
        {
            "category": "Жаргон",
            "terms": [
                {
                    "term": "Beast mode",
                    "definition": "Очень стойкий и проекционный аромат, который 'слышно' на большом расстоянии",
                    "examples": "Этот аромат просто beast mode - чувствуется весь день!",
                    "synonyms": "зверь, монстр стойкости"
                },
                {
                    "term": "Комплиментарный",
                    "definition": "Аромат, который часто получает положительные отзывы и комплименты от окружающих",
                    "examples": "Очень комплиментарный аромат, все спрашивают что это",
                    "synonyms": "compliment getter"
                },
                {
                    "term": "Флэнкер",
                    "definition": "Коммерческая вариация популярного аромата с изменениями в композиции",
                    "examples": "Новый флэнкер Chanel No.5 более свежий чем оригинал",
                    "synonyms": "flanker, вариация"
                }
            ]
        },
        
        # Концентрации
        {
            "category": "Концентрации",
            "terms": [
                {
                    "term": "EDT",
                    "definition": "Eau de Toilette - туалетная вода с концентрацией ароматических масел 5-15%",
                    "examples": "EDT обычно более легкая и свежая",
                    "synonyms": "туалетная вода"
                },
                {
                    "term": "EDP",
                    "definition": "Eau de Parfum - парфюмерная вода с концентрацией ароматических масел 15-20%",
                    "examples": "EDP держится дольше чем EDT",
                    "synonyms": "парфюмерная вода"
                },
                {
                    "term": "Parfum",
                    "definition": "Самая высокая концентрация ароматических масел 20-40%, также называется экстракт",
                    "examples": "Parfum - самая дорогая и стойкая форма",
                    "synonyms": "экстракт, духи"
                }
            ]
        },
        
        # Аксессуары
        {
            "category": "Аксессуары",
            "terms": [
                {
                    "term": "Атомайзер",
                    "definition": "Небольшой флакон для распыления парфюма, обычно объемом 5-15 мл",
                    "examples": "Залил любимый аромат в атомайзер для поездки",
                    "synonyms": "распылитель, travalo"
                },
                {
                    "term": "Тестер",
                    "definition": "Демонстрационная версия парфюма без коробки, обычно дешевле оригинала",
                    "examples": "Купил тестер - аромат тот же, но упаковки нет",
                    "synonyms": "демо версия"
                }
            ]
        }
    ]
    
    # Добавляем данные в базу
    for category_data in initial_data:
        category_name = category_data["category"]
        print(f"Добавляем категорию: {category_name}")
        
        for term_data in category_data["terms"]:
            db.add_term(
                term=term_data["term"],
                definition=term_data["definition"],
                category_name=category_name,
                examples=term_data.get("examples"),
                synonyms=term_data.get("synonyms")
            )
            print(f"  ✅ {term_data['term']}")
    
    print(f"База данных инициализирована! Добавлено {sum(len(cat['terms']) for cat in initial_data)} терминов")

if __name__ == "__main__":
    # Тестирование базы данных
    db = PerfumeDatabase()
    populate_initial_data(db)
    
    # Показываем статистику
    stats = db.get_stats()
    print(f"\n📊 Статистика:")
    print(f"Терминов: {stats['total_terms']}")
    print(f"Категорий: {stats['total_categories']}")
