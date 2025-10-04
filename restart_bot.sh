#!/bin/bash

echo "🔄 Перезапуск бота..."

# Убиваем все процессы Python с main.py
echo "📛 Останавливаем все экземпляры бота..."
pkill -f "python.*main.py" || true
killall python3 2>/dev/null || true

# Ждем 2 секунды для полной остановки
echo "⏳ Ждем завершения процессов..."
sleep 2

# Проверяем, что процессов нет
RUNNING=$(ps aux | grep "python.*main.py" | grep -v grep | wc -l)
if [ $RUNNING -gt 0 ]; then
    echo "⚠️  Найдены работающие процессы, принудительно завершаем..."
    pkill -9 -f "python.*main.py" || true
    sleep 1
fi

echo "✅ Все процессы остановлены"

# Запускаем бота
echo "🚀 Запускаем бота..."
python3 main.py

echo "🏁 Скрипт завершен"
