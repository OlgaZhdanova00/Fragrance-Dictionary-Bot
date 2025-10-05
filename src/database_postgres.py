"""
Модуль для работы с PostgreSQL базой данных
Содержит все функции для управления парфюмерными терминами
"""
import psycopg
from psycopg.rows import dict_row
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_URL

class PerfumeDatabase:
    def __init__(self, db_url: str = None):
        """Инициализация базы данных PostgreSQL"""
        self.db_url = db_url or DATABASE_URL
        self.init_database()
    
    def get_connection(self):
        """Создает соединение с PostgreSQL"""
        return psycopg.connect(self.db_url, row_factory=dict_row)
    
    def init_database(self):
        """Инициализация структуры базы данных"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Создаем таблицу категорий
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создаем таблицу терминов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS terms (
                        id SERIAL PRIMARY KEY,
                        term VARCHAR(200) NOT NULL,
                        definition TEXT NOT NULL,
                        category_id INTEGER REFERENCES categories(id),
                        synonyms TEXT,
                        usage_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создаем таблицу поисковых запросов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_logs (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        query VARCHAR(200) NOT NULL,
                        term_id INTEGER REFERENCES terms(id),
                        found BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создаем таблицу предложений пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_suggestions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        username VARCHAR(100),
                        term VARCHAR(200) NOT NULL,
                        definition TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
                # Добавляем начальные данные если база пуста
                cursor.execute('SELECT COUNT(*) FROM categories')
                if cursor.fetchone()['count'] == 0:
                    self._add_initial_data(cursor)
                    conn.commit()
    
    def _add_initial_data(self, cursor):
        """Добавляет начальные данные в базу"""
        # Категории
        categories = [
            ("Основы парфюмерии", "Базовые понятия и термины"),
            ("Ингредиенты", "Компоненты и составляющие ароматов"),
            ("Типы ароматов", "Классификация парфюмерных композиций"),
            ("Концентрации", "Виды парфюмерной продукции по концентрации"),
            ("Техники и процессы", "Методы создания и производства")
        ]
        
        for name, desc in categories:
            cursor.execute(
                'INSERT INTO categories (name, description) VALUES (%s, %s)',
                (name, desc)
            )
        
        # Термины
        terms_data = [
            ("Атомайзер", "Устройство для распыления парфюма в виде мелких капель", 2, "распылитель, пульверизатор"),
            ("Аккорд", "Гармоничное сочетание нескольких нот в парфюмерной композиции", 1, "гармония, созвучие"),
            ("Альдегиды", "Химические соединения, придающие аромату свежесть и искристость", 2, "альдегидные ноты"),
            ("Анималистические ноты", "Ароматы животного происхождения (мускус, амбра, цибет)", 2, "животные ноты"),
            ("Базовые ноты", "Основа аромата, самые стойкие компоненты композиции", 1, "база, шлейф"),
            ("Букет", "Сложная многогранная парфюмерная композиция", 3, "композиция, смесь"),
            ("Винтаж", "Парфюм, выпущенный в прошлые десятилетия, часто снятый с производства", 3, "ретро, старинный"),
            ("Головные ноты", "Первые ощущения от аромата, самые летучие компоненты", 1, "верхние ноты, топ"),
            ("Дистилляция", "Процесс получения эфирных масел путем перегонки с водяным паром", 5, "перегонка"),
            ("Енфлераж", "Старинный метод извлечения ароматов с помощью жиров", 5, "жировая экстракция"),
            ("Экстракт", "Самая концентрированная форма парфюма (20-40% ароматических веществ)", 4, "духи, parfum")
        ]
        
        for term, definition, cat_id, synonyms in terms_data:
            cursor.execute(
                'INSERT INTO terms (term, definition, category_id, synonyms) VALUES (%s, %s, %s, %s)',
                (term, definition, cat_id, synonyms)
            )
    
    def search_terms(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск терминов с разными стратегиями"""
        query_lower = query.lower().strip()
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Точное совпадение
                cursor.execute('''
                    SELECT t.*, c.name as category_name
                    FROM terms t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE LOWER(t.term) = %s
                    ORDER BY t.usage_count DESC
                ''', (query_lower,))
                
                exact_match = cursor.fetchall()
                if exact_match:
                    return list(exact_match)
                
                # 2. Поиск по синонимам
                cursor.execute('''
                    SELECT t.*, c.name as category_name
                    FROM terms t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.synonyms IS NOT NULL 
                    AND LOWER(t.synonyms) LIKE %s
                    ORDER BY t.usage_count DESC
                    LIMIT %s
                ''', (f'%{query_lower}%', limit))
                
                synonym_results = cursor.fetchall()
                if synonym_results:
                    return list(synonym_results)
                
                # 3. Частичное совпадение в названии
                cursor.execute('''
                    SELECT t.*, c.name as category_name
                    FROM terms t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE LOWER(t.term) LIKE %s
                    ORDER BY t.usage_count DESC
                    LIMIT %s
                ''', (f'%{query_lower}%', limit))
                
                partial_results = cursor.fetchall()
                if partial_results:
                    return list(partial_results)
                
                # 4. Поиск в определениях
                cursor.execute('''
                    SELECT t.*, c.name as category_name
                    FROM terms t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE LOWER(t.definition) LIKE %s
                    ORDER BY t.usage_count DESC
                    LIMIT %s
                ''', (f'%{query_lower}%', limit))
                
                definition_results = cursor.fetchall()
                return list(definition_results)
    
    def get_random_term(self) -> Optional[Dict]:
        """Получает случайный термин"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT t.*, c.name as category_name
                    FROM terms t
                    LEFT JOIN categories c ON t.category_id = c.id
                    ORDER BY RANDOM()
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                return result if result else None
    
    def get_categories(self) -> List[Dict]:
        """Получает все категории"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT c.*, COUNT(t.id) as terms_count
                    FROM categories c
                    LEFT JOIN terms t ON c.id = t.category_id
                    GROUP BY c.id, c.name, c.description, c.created_at
                    ORDER BY c.name
                ''')
                return list(cursor.fetchall())
    
    def get_terms_by_category(self, category_id: int) -> List[Dict]:
        """Получает термины по категории"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT t.*, c.name as category_name
                    FROM terms t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.category_id = %s
                    ORDER BY t.term
                ''', (category_id,))
                return list(cursor.fetchall())
    
    def increment_usage(self, term_id: int):
        """Увеличивает счетчик использования термина"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'UPDATE terms SET usage_count = usage_count + 1 WHERE id = %s',
                    (term_id,)
                )
                conn.commit()
    
    def log_search(self, user_id: int, query: str, term_id: int = None, found: bool = False):
        """Логирует поисковый запрос"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO search_logs (user_id, query, term_id, found)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, query, term_id, found))
                conn.commit()
    
    def add_user_suggestion(self, user_id: int, username: str, term: str, definition: str):
        """Добавляет предложение пользователя"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_suggestions (user_id, username, term, definition)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, username, term, definition))
                conn.commit()
    
    def get_stats(self) -> Dict:
        """Получает статистику базы данных"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) as count FROM terms')
                total_terms = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM categories')
                total_categories = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM search_logs')
                total_searches = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM user_suggestions WHERE status = %s', ('pending',))
                pending_suggestions = cursor.fetchone()['count']
                
                return {
                    'total_terms': total_terms,
                    'total_categories': total_categories,
                    'total_searches': total_searches,
                    'pending_suggestions': pending_suggestions
                }
    
    def get_database_stats(self) -> Dict:
        """Алиас для get_stats() для совместимости"""
        return self.get_stats()
    
    def close(self):
        """Закрытие соединения с базой данных (для совместимости)"""
        # PostgreSQL соединения закрываются автоматически при использовании контекстного менеджера
        pass
