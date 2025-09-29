# 🚀 Полное руководство по деплою бота на Render

## 📋 Шаг 1: Подготовка к деплою

### 1.1 Создание GitHub репозитория

1. **Зайдите на [github.com](https://github.com)**
2. **Нажмите "New repository"**
3. **Настройки репозитория:**
   - Name: `perfume-calendar-bot`
   - Visibility: `Private` (рекомендуется)
   - ✅ Add a README file
   - ✅ Add .gitignore (выберите Python)

4. **Создайте репозиторий**

### 1.2 Загрузка кода в GitHub

```bash
# В папке проекта выполните:
git init
git add .
git commit -m "Initial commit: Perfume Dictionary Bot"
git branch -M main
git remote add origin https://github.com/ВАШ_USERNAME/perfume-calendar-bot.git
git push -u origin main
```

## 📋 Шаг 2: Настройка Render

### 2.1 Создание аккаунта и подключение GitHub

1. **Зайдите на [render.com](https://render.com)**
2. **Зарегистрируйтесь через GitHub** (рекомендуется)
3. **Подтвердите аккаунт по email**

### 2.2 Создание Web Service

1. **На главной странице Render нажмите "New +"**
2. **Выберите "Web Service"**
3. **Connect GitHub repository:**
   - Найдите `perfume-calendar-bot`
   - Нажмите "Connect"

### 2.3 Настройки деплоя

**Основные настройки:**
- **Name:** `perfume-calendar-bot`
- **Environment:** `Python 3`
- **Region:** `Oregon (US West)` или ближайший к вам
- **Branch:** `main`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`

**Расширенные настройки:**
- **Auto-Deploy:** ✅ Yes (автообновление при изменениях в GitHub)

## 📋 Шаг 3: Настройка переменных окружения

В разделе **Environment Variables** добавьте:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | `8248837045:AAHH7CIqP_TTmW06lPx8paTPvBOJEC31VtA` |
| `ADMIN_USER_IDS` | `438418422` |
| `DATABASE_PATH` | `data/database.db` |
| `LOG_LEVEL` | `INFO` |
| `DEBUG` | `False` |

⚠️ **ВАЖНО:** Никогда не заливайте `.env` файл в GitHub!

## 📋 Шаг 4: Настройка персистентного диска

1. **В настройках сервиса найдите "Disks"**
2. **Нажмите "Add Disk"**
3. **Настройки диска:**
   - **Name:** `data`
   - **Mount Path:** `/opt/render/project/src/data`
   - **Size:** `1 GB` (достаточно для SQLite)

## 📋 Шаг 5: Деплой и тестирование

### 5.1 Запуск деплоя

1. **Нажмите "Create Web Service"**
2. **Дождитесь завершения сборки** (5-10 минут)
3. **Проверьте логи** на наличие ошибок

### 5.2 Тестирование бота

1. **Найдите бота:** `@Fragrance_dictionary_bot`
2. **Отправьте `/start`**
3. **Протестируйте все функции:**
   - Поиск терминов
   - Случайные термины
   - Категории
   - Предложения новых терминов

## 📋 Шаг 6: Мониторинг и управление

### 6.1 Просмотр логов

- **В панели Render:** вкладка "Logs"
- **Мониторинг ошибок** и активности пользователей

### 6.2 Обновления

- **Автоматически:** при push в GitHub
- **Вручную:** кнопка "Manual Deploy"

### 6.3 Управление ресурсами

- **Стоимость:** Бесплатный план (512MB RAM, ограничения)
- **Upgrade:** При росте нагрузки

## 🎯 Итоговая схема работы

```
Пользователь → @Fragrance_dictionary_bot → Render Server → SQLite Database
                                                ↓
                                        Ваш Telegram канал (упоминания)
```

## 🔧 Решение проблем

### Проблема: Бот не отвечает
- Проверьте логи в Render
- Убедитесь, что BOT_TOKEN правильный
- Проверьте статус сервиса

### Проблема: База данных пустая
- Убедитесь, что персистентный диск настроен
- Проверьте права доступа к папке data

### Проблема: Ошибки при деплое
- Проверьте requirements.txt
- Убедитесь, что все файлы загружены в GitHub

## 📞 Поддержка

- **Render Docs:** [render.com/docs](https://render.com/docs)
- **Telegram Bot API:** [core.telegram.org/bots](https://core.telegram.org/bots)
