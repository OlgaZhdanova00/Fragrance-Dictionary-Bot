"""
Конфигурация бота для платформы Render
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки Telegram бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN не установлен. Для локального тестирования создайте .env файл.")
    BOT_TOKEN = "dummy_token_for_testing"

# Администраторы бота (ID пользователей Telegram)
ADMIN_USER_IDS_STR = os.getenv('ADMIN_USER_IDS', '')
ADMIN_USER_IDS = []
if ADMIN_USER_IDS_STR:
    try:
        ADMIN_USER_IDS = [int(user_id.strip()) for user_id in ADMIN_USER_IDS_STR.split(',') if user_id.strip()]
    except ValueError:
        print("⚠️ Ошибка в формате ADMIN_USER_IDS. Используйте формат: 123456789,987654321")

# Настройки базы данных
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/database.db')
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL connection string

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Настройки для Render
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Проверяем что все критичные настройки установлены
def validate_config():
    """Проверяет корректность конфигурации"""
    if not BOT_TOKEN:
        return False, "BOT_TOKEN не установлен"
    
    if not ADMIN_USER_IDS:
        print("⚠️ ADMIN_USER_IDS не установлены. Административные функции будут недоступны.")
    
    return True, "Конфигурация корректна"

if __name__ == "__main__":
    is_valid, message = validate_config()
    print(f"Статус конфигурации: {message}")
    print(f"BOT_TOKEN установлен: {'✅' if BOT_TOKEN else '❌'}")
    print(f"Администраторов: {len(ADMIN_USER_IDS)}")
    print(f"Путь к БД: {DATABASE_PATH}")
    print(f"Порт: {PORT}")
