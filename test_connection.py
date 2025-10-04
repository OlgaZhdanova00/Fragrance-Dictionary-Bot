#!/usr/bin/env python3
"""
Простой тест соединения с Telegram API
"""
import requests
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    exit(1)

def test_connection():
    """Тестируем соединение с API"""
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    print("🔍 Тестируем соединение...")
    
    # Получаем информацию о боте
    response = requests.get(f"{base_url}/getMe")
    if response.status_code == 200:
        bot_info = response.json()['result']
        print(f"✅ Бот подключен: {bot_info['first_name']} (@{bot_info['username']})")
    else:
        print(f"❌ Ошибка подключения: {response.text}")
        return False
    
    # Проверяем getUpdates (НЕ в long polling режиме)
    print("🔍 Проверяем getUpdates...")
    response = requests.post(f"{base_url}/getUpdates", json={"timeout": 1, "limit": 1})
    
    if response.status_code == 200:
        print("✅ getUpdates работает! Конфликтов нет.")
        return True
    elif response.status_code == 409:
        print("❌ 409 Conflict - другой процесс использует getUpdates!")
        print("Ответ:", response.text)
        return False
    else:
        print(f"⚠️ Неожиданный ответ: {response.status_code}")
        print("Ответ:", response.text)
        return False

if __name__ == "__main__":
    test_connection()
