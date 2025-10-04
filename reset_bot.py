#!/usr/bin/env python3
"""
Скрипт для сброса состояния бота и очистки webhook
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

def reset_bot():
    """Сбрасываем состояние бота"""
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    print("🔄 Сбрасываем webhook...")
    # Удаляем webhook (если есть)
    response = requests.post(f"{base_url}/deleteWebhook")
    if response.status_code == 200:
        print("✅ Webhook удален")
    else:
        print(f"⚠️ Ошибка удаления webhook: {response.text}")
    
    print("🔄 Получаем и пропускаем все обновления...")
    # Получаем все pending обновления и пропускаем их
    response = requests.post(f"{base_url}/getUpdates", json={"offset": -1})
    if response.status_code == 200:
        updates = response.json().get('result', [])
        if updates:
            last_update_id = updates[-1]['update_id']
            # Пропускаем все обновления
            requests.post(f"{base_url}/getUpdates", json={"offset": last_update_id + 1})
            print(f"✅ Пропущено {len(updates)} обновлений")
        else:
            print("✅ Нет pending обновлений")
    else:
        print(f"⚠️ Ошибка получения обновлений: {response.text}")
    
    print("✅ Состояние бота сброшено!")

if __name__ == "__main__":
    reset_bot()
