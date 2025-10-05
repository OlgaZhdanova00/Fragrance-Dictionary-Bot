"""
Главный файл бота "Парфюмерный календарь"
Telegram-бот для поиска и объяснения парфюмерных терминов
"""
import logging
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Добавляем папку src в path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import BOT_TOKEN, ADMIN_USER_IDS, validate_config, DEBUG
from src.database import PerfumeDatabase

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not DEBUG else logging.DEBUG
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = PerfumeDatabase()

class PerfumeBot:
    def __init__(self):
        """Инициализация бота"""
        self.db = db
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        welcome_text = f"""
🌸 Добро пожаловать в *Парфюмерный календарь*!

Привет, {user.first_name}! Я помогу вам разобраться в мире парфюмерии.

📚 *Как использовать:*
• Просто напишите любой парфюмерный термин для поиска
• Нажимайте на кнопки для быстрого доступа к функциям
• Изучайте случайные термины
• Предлагайте новые термины для словаря
        """
        
        # Создаем клавиатуру с основными функциями
        keyboard = [
            [
                InlineKeyboardButton("🎲 Случайный термин", callback_data="random"),
                InlineKeyboardButton("📚 Категории", callback_data="categories")
            ],
            [
                InlineKeyboardButton("💡 Предложить термин", callback_data="suggest"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
            ]
        ]
        inline_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=inline_markup
        )
        
        # Инструкция по доступу к меню
        await update.message.reply_text(
            "💡 *Как вернуться к главному меню:*\n"
            "📱 На телефоне: нажмите ☰ (три полоски) слева от строки ввода\n"
            "💻 На компьютере: напишите `/start` или `/help`",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Логируем статистику
        logger.info(f"Новый пользователь: {user.id} (@{user.username})")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 *Справка по боту "Парфюмерный календарь"*

🔍 *Поиск терминов:*
Просто напишите мне любое слово или термин из мира парфюмерии, и я объясню его значение.

Примеры: "верхние ноты", "beast mode", "атомайзер"

📋 *Функции бота:*
🏠 Главное меню - возврат к основным функциям
ℹ️ Справка - как пользоваться ботом
🎲 Случайный термин - изучение новых понятий
📚 Категории - просмотр терминов по темам
💡 Предложить термин - добавление новых слов
📊 Статистика - информация о базе данных

🎯 *Поиск работает по:*
• Точному названию термина
• Синонимам и альтернативным названиям
• Частичным совпадениям
• Содержимому определений

💡 *Хотите помочь?*
Используйте кнопку "💡 Предложить термин" чтобы предложить новый термин или улучшение существующего.

❓ *Не нашли термин?*
Напишите администратору канала @your_admin или воспользуйтесь кнопкой "💡 Предложить термин"
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def random_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /random - случайный термин"""
        random_term = self.db.get_random_term()
        
        if not random_term:
            await update.message.reply_text("❌ База данных пуста. Обратитесь к администратору.")
            return
        
        await self.send_term_info(update, random_term, is_random=True)

    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /categories"""
        categories = self.db.get_categories()
        
        if not categories:
            await update.message.reply_text("❌ Категории не найдены.")
            return
        
        text = "📚 *Категории терминов:*\n\n"
        keyboard = []
        
        for category in categories:
            # Считаем количество терминов в категории
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT COUNT(*) as count FROM terms WHERE category_id = ?',
                    (category['id'],)
                )
                count = cursor.fetchone()['count']
            
            text += f"🏷️ *{category['name']}* ({count} терминов)\n"
            if category['description']:
                text += f"   {category['description']}\n"
            text += "\n"
            
            # Добавляем кнопку для каждой категории
            keyboard.append([
                InlineKeyboardButton(
                    f"📖 {category['name']} ({count})",
                    callback_data=f"category_{category['id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает статистику базы данных"""
        stats = self.db.get_stats()
        
        text = f"""
📊 *Статистика парфюмерного словаря:*

📚 Всего терминов: *{stats['total_terms']}*
🏷️ Категорий: *{stats['total_categories']}*
🔍 Поисков за неделю: *{stats['searches_week']}*
💡 Ожидает модерации: *{stats['pending_suggestions']}*

🔥 *Популярные термины:*
        """
        
        if stats['popular_terms']:
            for i, term in enumerate(stats['popular_terms'], 1):
                text += f"{i}. {term['term']} ({term['usage_count']} запросов)\n"
        else:
            text += "Пока нет статистики по запросам"
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def search_terms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик поиска терминов по тексту сообщения"""
        query = update.message.text.strip()
        user_id = update.effective_user.id
        
        
        # Игнорируем команды
        if query.startswith('/'):
            return
        
        logger.info(f"Поиск термина: '{query}' пользователем {user_id}")
        
        # Ищем термины
        results = self.db.search_terms(query)
        
        if not results:
            # Логируем неуспешный поиск
            self.db.log_search(user_id, query, found=False)
            
            await update.message.reply_text(
                f"❌ Термин '*{query}*' не найден.\n\n"
                "💡 Попробуйте:\n"
                "• Проверить написание\n"
                "• Использовать синонимы\n"
                "• Посмотреть категории через кнопку \"📚 Категории\"\n"
                "• Предложить новый термин: кнопка \"💡 Предложить термин\"",
                parse_mode='Markdown'
            )
            return
        
        if len(results) == 1:
            # Найден один термин - показываем его
            term = results[0]
            self.db.log_search(user_id, query, term['id'], found=True)
            self.db.increment_usage(term['id'])
            await self.send_term_info(update, term)
        else:
            # Найдено несколько терминов - показываем список
            text = f"🔍 По запросу '*{query}*' найдено {len(results)} терминов:\n\n"
            keyboard = []
            
            for i, term in enumerate(results[:10], 1):  # Показываем максимум 10
                text += f"{i}. *{term['term']}*"
                if term['category_name']:
                    text += f" ({term['category_name']})"
                text += "\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{i}. {term['term']}",
                        callback_data=f"term_{term['id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="start")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    async def send_term_info(self, update: Update, term: dict, is_random: bool = False):
        """Отправляет информацию о термине"""
        # Форматируем информацию о термине
        text = f"📚 *{term['term']}*\n\n"
        
        # Определение
        text += f"📖 {term['definition']}\n\n"
        
        # Категория
        if term['category_name']:
            text += f"🏷️ *Категория:* {term['category_name']}\n"
        
        # Примеры
        if term['examples']:
            text += f"💡 *Примеры:* {term['examples']}\n"
        
        # Синонимы
        if term['synonyms']:
            text += f"🔄 *Синонимы:* {term['synonyms']}\n"
        
        # Статистика использования
        if term['usage_count'] > 0:
            text += f"📊 *Запросов:* {term['usage_count']}\n"
        
        # Создаем клавиатуру
        keyboard = [
            [
                InlineKeyboardButton("🎲 Другой случайный", callback_data="random"),
                InlineKeyboardButton("📚 Категории", callback_data="categories")
            ]
        ]
        
        if not is_random:
            keyboard.append([
                InlineKeyboardButton("🏠 Главное меню", callback_data="start")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "start":
            await self.start_callback(update, context)
        elif data == "help":
            await self.help_callback(update, context)
        elif data == "random":
            await self.random_callback(update, context)
        elif data == "categories":
            await self.categories_callback(update, context)
        elif data.startswith("category_"):
            category_id = int(data.split("_")[1])
            await self.show_category_terms(update, category_id)
        elif data.startswith("term_"):
            term_id = int(data.split("_")[1])
            await self.show_term_by_id(update, term_id)
        elif data == "suggest":
            await self.suggest_callback(update, context)
        elif data == "stats":
            await self.stats_callback(update, context)

    async def start_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для кнопки 'Главное меню'"""
        user = update.effective_user
        
        welcome_text = f"""
🌸 *Парфюмерный календарь*

Привет, {user.first_name}! Чем могу помочь?

🔍 Напишите любой парфюмерный термин или выберите действие:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🎲 Случайный термин", callback_data="random"),
                InlineKeyboardButton("📚 Категории", callback_data="categories")
            ],
            [
                InlineKeyboardButton("💡 Предложить термин", callback_data="suggest"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
            ]
        ]
        inline_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=inline_markup
        )

    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для кнопки 'Помощь'"""
        help_text = """
📖 *Как пользоваться ботом:*

🔍 *Поиск:* Просто напишите термин
💡 *Предложить:* Нажмите кнопку "💡 Предложить термин"
🎲 *Изучать:* Нажимайте "Случайный термин"
📚 *Категории:* Просматривайте по темам

*Примеры запросов:*
• "верхние ноты"
• "beast mode" 
• "атомайзер"
• "флэнкер"
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def random_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для кнопки 'Случайный термин'"""
        random_term = self.db.get_random_term()
        
        if random_term:
            await self.send_term_info(update, random_term, is_random=True)
        else:
            await update.callback_query.edit_message_text("❌ Термины не найдены")

    async def categories_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для кнопки 'Категории'"""
        categories = self.db.get_categories()
        
        if not categories:
            await update.callback_query.edit_message_text("❌ Категории не найдены.")
            return
        
        text = "📚 *Категории терминов:*\n\n"
        keyboard = []
        
        for category in categories:
            # Считаем количество терминов в категории
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT COUNT(*) as count FROM terms WHERE category_id = ?',
                    (category['id'],)
                )
                count = cursor.fetchone()['count']
            
            text += f"🏷️ *{category['name']}* ({count} терминов)\n"
            if category['description']:
                text += f"   {category['description']}\n"
            text += "\n"
            
            # Добавляем кнопку для каждой категории
            keyboard.append([
                InlineKeyboardButton(
                    f"📖 {category['name']} ({count})",
                    callback_data=f"category_{category['id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def suggest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /suggest для предложения термина"""
        text = """
💡 *Предложите новый термин!*

Отправьте сообщение в формате:
```
Название термина
Объяснение термина
Категория (необязательно)
Примеры использования (необязательно)
```

*Пример:*
```
Винтаж
Старый, редкий аромат из прошлых лет
Жаргон
"Этот винтаж 80-х годов стоит целое состояние"
```

Ваше предложение будет рассмотрено администратором.
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')

    async def suggest_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для кнопки 'Предложить термин'"""
        text = """
💡 *Предложите новый термин!*

Отправьте сообщение в формате:
```
Название термина
Объяснение термина
Категория (необязательно)
Примеры использования (необязательно)
```

*Пример:*
```
Винтаж
Старый, редкий аромат из прошлых лет
Жаргон
"Этот винтаж 80-х годов стоит целое состояние"
```

Ваше предложение будет рассмотрено администратором.
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def show_category_terms(self, update: Update, category_id: int):
        """Показывает термины из выбранной категории"""
        # Получаем информацию о категории
        with self.db.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
            category = cursor.fetchone()
            
            if not category:
                await update.callback_query.edit_message_text("❌ Категория не найдена")
                return
            
            # Получаем термины этой категории
            cursor = conn.execute('''
                SELECT * FROM terms 
                WHERE category_id = ? 
                ORDER BY term
            ''', (category_id,))
            terms = cursor.fetchall()
        
        if not terms:
            text = f"📚 *{category['name']}*\n\nВ этой категории пока нет терминов."
        else:
            text = f"📚 *{category['name']}* ({len(terms)} терминов)\n\n"
            
            keyboard = []
            for term in terms[:15]:  # Максимум 15 терминов
                text += f"• {term['term']}\n"
                keyboard.append([
                    InlineKeyboardButton(
                        f"📖 {term['term']}",
                        callback_data=f"term_{term['id']}"
                    )
                ])
            
            if len(terms) > 15:
                text += f"\n... и еще {len(terms) - 15} терминов"
        
        keyboard = keyboard or []
        keyboard.append([
            InlineKeyboardButton("📚 Все категории", callback_data="categories"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="start")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для кнопки 'Статистика'"""
        stats = self.db.get_database_stats()
        
        stats_text = f"""
📊 *Статистика парфюмерного словаря*

📚 Всего терминов: *{stats['total_terms']}*
🏷️ Категорий: *{stats['total_categories']}*
🔍 Поисков за неделю: *{stats['searches_week']}*
💡 Ожидает модерации: *{stats['pending_suggestions']}*

🔥 *Популярные термины:*
        """
        
        # Добавляем популярные термины если есть
        if stats.get('popular_terms'):
            for i, term in enumerate(stats['popular_terms'][:5], 1):
                stats_text += f"{i}. {term['term']} ({term['usage_count']} запросов)\n"
        else:
            stats_text += "Пока нет данных о популярности терминов"
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            stats_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def show_term_by_id(self, update: Update, term_id: int):
        """Показывает термин по ID"""
        term = self.db.get_term_by_id(term_id)
        
        if term:
            # Увеличиваем счетчик использования
            self.db.increment_usage(term_id)
            await self.send_term_info(update, term)
        else:
            await update.callback_query.edit_message_text("❌ Термин не найден")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
            )

async def setup_bot_commands(application):
    """Настройка команд бота для отображения в меню"""
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("help", "ℹ️ Справка по использованию")
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Команды бота настроены")

def main():
    """Главная функция запуска бота"""
    import fcntl
    import sys
    
    # Временно отключаем lock-механизм для решения конфликта
    logger.info("🚀 Запуск бота...")
    
    # Настройка продакшена при первом запуске
    if not os.path.exists("data"):
        os.makedirs("data")
        logger.info("Создана папка data")
    
    # Инициализация базы данных при первом запуске
    try:
        db_test = PerfumeDatabase()
        stats = db_test.get_database_stats()
        if stats['total_terms'] == 0:
            logger.info("База данных пуста, инициализируем начальные данные...")
            # Здесь база данных уже инициализирована в __init__
        logger.info(f"База данных готова: {stats['total_terms']} терминов")
        db_test.close()
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        return
    
    # Проверяем конфигурацию
    is_valid, message = validate_config()
    if not is_valid:
        logger.error(f"Ошибка конфигурации: {message}")
        return
    
    logger.info("Запуск бота 'Парфюмерный календарь'...")
    
    # Создаем экземпляр бота
    bot = PerfumeBot()
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд (английские и русские)
    # Только основная команда /start (остальные скрыты - только через кнопки)
    app.add_handler(CommandHandler("start", bot.start_command))
    
    # Обработчик кнопок
    app.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Обработчик текстовых сообщений (поиск терминов)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.search_terms))
    
    # Обработчик ошибок
    app.add_error_handler(bot.error_handler)
    
    logger.info("Бот готов к работе!")
    
    # Настраиваем команды бота
    async def post_init(application):
        await setup_bot_commands(application)
    
    app.post_init = post_init
    
    # Запускаем бота
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
