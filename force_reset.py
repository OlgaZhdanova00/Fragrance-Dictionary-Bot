#!/usr/bin/env python3
"""
Принудительный сброс всех соединений бота
"""
import requests
import os
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

def force_reset():
    """Принудительно сбрасываем все соединения"""
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    print("💥 ПРИНУДИТЕЛЬНЫЙ СБРОС ВСЕХ СОЕДИНЕНИЙ...")
    
    # 1. Удаляем webhook принудительно
    print("🗑️ Удаляем webhook...")
    response = requests.post(f"{base_url}/deleteWebhook", json={"drop_pending_updates": True})
    print(f"Webhook: {response.json()}")
    
    # 2. Получаем и пропускаем ВСЕ pending updates
    print("🧹 Очищаем все pending updates...")
    for i in range(10):  # максимум 10 итераций
        response = requests.post(f"{base_url}/getUpdates", 
                               json={"offset": -1, "timeout": 1})
        if response.status_code == 200:
            updates = response.json().get('result', [])
            if updates:
                last_id = updates[-1]['update_id']
                # Пропускаем все
                skip_response = requests.post(f"{base_url}/getUpdates", 
                                           json={"offset": last_id + 1, "timeout": 1})
                print(f"Итерация {i+1}: пропущено {len(updates)} updates")
            else:
                print(f"Итерация {i+1}: нет updates")
                break
        elif response.status_code == 409:
            print(f"Итерация {i+1}: 409 Conflict - ждем...")
            time.sleep(5)
        else:
            print(f"Итерация {i+1}: ошибка {response.status_code}")
            break
    
    # 3. Финальная проверка
    print("🔍 Финальная проверка...")
    response = requests.post(f"{base_url}/getUpdates", json={"timeout": 1, "limit": 1})
    
    if response.status_code == 200:
        print("✅ УСПЕХ! Конфликт устранен!")
        return True
    else:
        print(f"❌ Конфликт остался: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    force_reset()
