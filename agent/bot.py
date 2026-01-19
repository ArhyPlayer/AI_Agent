#!/usr/bin/env python3
"""
AI Agent Telegram Bot
Telegram интерфейс для AI агента
"""

import os
import logging
from dotenv import load_dotenv
import telebot
from telebot import types
from agent import AIAgent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN or BOT_TOKEN == "your-telegram-bot-token-here":
    raise ValueError(
        "TELEGRAM_BOT_TOKEN не настроен!\n"
        "Создайте бота через @BotFather и добавьте токен в .env файл"
    )

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения агентов для каждого пользователя
user_agents = {}


def get_user_agent(user_id: int) -> AIAgent:
    """Получить или создать агента для пользователя"""
    if user_id not in user_agents:
        logger.info(f"Создание нового агента для пользователя {user_id}")
        user_agents[user_id] = AIAgent()
    return user_agents[user_id]


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = """
🤖 *AI Agent - Ваш умный ассистент*

Я могу помочь вам с различными задачами:

🌤️ *Погода* - "Какая погода в Москве?"
💰 *Криптовалюты* - "Цена биткоина"
🔍 *Поиск* - "Найди информацию о Python"
📁 *Файлы* - "Создай файл data.txt"
🌐 *HTTP запросы* - "Сделай GET запрос"
💻 *Команды* - "Выполни команду ls"

📝 *Доступные команды:*
/start - Начать работу
/help - Показать справку
/clear - Очистить историю разговора
/history - Показать историю

Просто отправьте мне сообщение и я помогу вам! 😊
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')


@bot.message_handler(commands=['clear'])
def clear_history(message):
    """Очистить историю разговора пользователя"""
    user_id = message.from_user.id
    if user_id in user_agents:
        user_agents[user_id].clear_memory()
        bot.reply_to(message, "✅ История разговора очищена!")
    else:
        bot.reply_to(message, "История уже пуста!")


@bot.message_handler(commands=['history'])
def show_history(message):
    """Показать историю разговора"""
    user_id = message.from_user.id
    agent = get_user_agent(user_id)
    
    history = agent.get_conversation_history()
    
    if not history:
        bot.reply_to(message, "📝 История разговора пуста")
        return
    
    history_text = "📝 История разговора:\n\n"
    for i, msg in enumerate(history[-10:], 1):  # Последние 10 сообщений
        role = "👤 Вы" if msg['role'] == 'user' else "🤖 Агент"
        # Берем только первые 100 символов
        content = msg['content'][:100]
        if len(msg['content']) > 100:
            content += "..."
        # Экранируем специальные символы Markdown (используем raw strings)
        content = content.replace('_', r'\_').replace('*', r'\*').replace('[', r'\[').replace('`', r'\`')
        history_text += f"{i}. {role}: {content}\n\n"
    
    # Убираем parse_mode чтобы избежать ошибок парсинга
    bot.reply_to(message, history_text)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработчик всех текстовых сообщений"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    user_text = message.text
    
    logger.info(f"Получено сообщение от {user_name} ({user_id}): {user_text}")
    
    # Отправляем "печатает..."
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Получаем агента для пользователя
        agent = get_user_agent(user_id)
        
        # Обрабатываем запрос
        response = agent.process_query(user_text)
        
        # Отправляем ответ
        # Разбиваем длинные сообщения
        if len(response) > 4000:
            # Telegram ограничивает сообщения до 4096 символов
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                bot.send_message(message.chat.id, part)
        else:
            bot.send_message(message.chat.id, response)
        
        logger.info(f"Ответ отправлен пользователю {user_id}")
        
    except Exception as e:
        error_msg = f"❌ Произошла ошибка: {str(e)}"
        logger.error(f"Ошибка при обработке сообщения от {user_id}: {e}", exc_info=True)
        bot.reply_to(message, error_msg)


@bot.message_handler(content_types=['document', 'photo', 'audio', 'video'])
def handle_file(message):
    """Обработчик файлов"""
    bot.reply_to(
        message,
        "📎 Извините, я пока не умею работать с файлами через Telegram.\n"
        "Используйте текстовые команды для работы с файлами на сервере."
    )


def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск Telegram бота...")
    
    try:
        # Проверяем подключение
        bot_info = bot.get_me()
        logger.info(f"✅ Бот запущен: @{bot_info.username}")
        logger.info(f"📝 Имя бота: {bot_info.first_name}")
        
        # Запускаем polling
        logger.info("⏳ Ожидание сообщений...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
    except KeyboardInterrupt:
        logger.info("\n👋 Остановка бота...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

