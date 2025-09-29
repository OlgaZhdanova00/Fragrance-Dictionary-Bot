# 🚀 Инструкции по деплою бота на Render

## 📋 Подготовка к деплою

### 1. Создание репозитория GitHub

1. **Создайте новый репозиторий на GitHub:**
   - Назовите его `perfume-calendar-bot`
   - Сделайте его приватным (рекомендуется)

2. **Загрузите код в GitHub:**
   ```bash
   # В папке проекта
   git init
   git add .
   git commit -m "Initial commit: Perfume Dictionary Bot"
   git branch -M main
   git remote add origin https://github.com/ВАШ_USERNAME/perfume-calendar-bot.git
   git push -u origin main
   ```

### 2. Настройка Render

1. **Зайдите на [render.com](https://render.com)**
2. **Подключите GitHub аккаунт**
3. **Создайте новый Web Service:**
   - Connect Repository → выберите ваш репозиторий
   - Name: `perfume-calendar-bot`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

### 3. Настройка переменных окружения в Render

В разделе **Environment Variables** добавьте:

```
BOT_TOKEN=8248837045:AAHH7CIqP_TTmW06lPx8paTPvBOJEC31VtA
ADMIN_USER_IDS=438418422
DATABASE_PATH=data/database.db
LOG_LEVEL=INFO
DEBUG=False
```

### 4. Деплой

1. **Нажмите "Create Web Service"**
2. **Render автоматически:**
   - Скачает код с GitHub
   - Установит зависимости
   - Запустит бота

## 📱 Использование бота

### Вариант 1: Личный бот
- Пользователи находят бота: @Fragrance_dictionary_bot
- Пишут `/start` и используют функции
- Предлагают новые термины

### Вариант 2: Бот в канале
1. **Добавьте бота в канал:**
   - Настройки канала → Администраторы
   - Добавить администратора → @Fragrance_dictionary_bot
   - Дайте права на отправку сообщений

2. **Настройте упоминания:**
   - Пользователи пишут: `@Fragrance_dictionary_bot атомайзер`
   - Бот отвечает с определением

## 🔄 Автоматические обновления

**При изменении кода:**
1. Делаете изменения локально
2. `git add .` → `git commit -m "описание"` → `git push`
3. Render автоматически перезапускает бота

## 📊 Мониторинг

**В панели Render видно:**
- Логи работы бота
- Статус (онлайн/офлайн)
- Использование ресурсов
- Ошибки

## 🆘 Решение проблем

### Бот не запускается:
1. Проверьте логи в Render
2. Убедитесь, что переменные окружения заданы
3. Проверьте токен бота в @BotFather

### Бот не отвечает:
1. Проверьте, что бот запущен в Render
2. Убедитесь, что токен действителен
3. Проверьте логи на ошибки

## 📈 Масштабирование

**Для больших нагрузок:**
- Render автоматически выделяет ресурсы
- Можно увеличить план при необходимости
- База данных SQLite подходит до ~1000 пользователей
