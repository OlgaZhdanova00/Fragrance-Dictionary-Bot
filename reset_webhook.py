#!/usr/bin/env python3
"""
Скрипт для сброса webhook и очистки pending updates
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN', '8248837045:AAHS7gxD-8WJxI-TJzHwDh8BwFgXE1pXamE')

async def reset_bot_state():
    print("🔄 Сбрасываем состояние бота...")
    async with httpx.AsyncClient() as client:
        # 1. Удаляем webhook
        response = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
        print(f"✅ Webhook удален: {response.json()}")
        
        # 2. Очищаем pending updates
        offset = 0
        updates_cleared = 0
        for i in range(3):
            response = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", 
                                       json={"offset": offset, "limit": 100, "timeout": 1})
            data = response.json()
            if not data['ok'] or not data['result']:
                break
            
            updates = data['result']
            if not updates:
                break
            
            for update in updates:
                offset = max(offset, update['update_id'] + 1)
            updates_cleared += len(updates)
            print(f"Очищено {len(updates)} обновлений")
        
        print(f"✅ Всего очищено {updates_cleared} pending обновлений")
        print("✅ Состояние бота сброшено!")

if __name__ == "__main__":
    asyncio.run(reset_bot_state())
