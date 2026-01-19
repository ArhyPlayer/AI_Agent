#!/usr/bin/env python3
"""
AI Agent - Терминальный ассистент с инструментами

Запуск: python run.py
"""

import os
import sys
import argparse
from agent import AIAgent, SimpleAgent
from dotenv import load_dotenv


def print_banner():
    """Выводит приветственное сообщение"""
    banner = """
    ╔══════════════════════════════════════════════╗
    ║              🤖 AI AGENT 🤖                  ║
    ║     Терминальный ассистент с инструментами   ║
    ╚══════════════════════════════════════════════╝

    Доступные команды:
    • help - показать справку
    • clear - очистить память
    • history - показать историю разговора
    • exit/quit - выйти

    Примеры запросов:
    • "Какая погода в Москве?"
    • "Сколько стоит Bitcoin?"
    • "Найди информацию о Python"
    • "Покажи файлы в текущей директории"
    • "Создай файл test.txt с текстом 'Hello World'"

    """
    print(banner)


def print_help():
    """Выводит справку по использованию"""
    help_text = """
    📚 СПРАВКА ПО ИСПОЛЬЗОВАНИЮ AI AGENT

    ОСНОВНЫЕ КОМАНДЫ:
    help     - показать эту справку
    clear    - очистить историю разговора
    history  - показать историю разговора
    exit     - выйти из программы

    ДОСТУПНЫЕ ИНСТРУМЕНТЫ:

    🌤️  ПОГОДА:
    "Какая погода в [город]?"
    "Погода в Санкт-Петербурге"

    💰 КРИПТОВАЛЮТА:
    "Цена биткоина"
    "Сколько стоит Ethereum в рублях?"
    "get_crypto_price bitcoin usd"

    🔍 ПОИСК В ИНТЕРНЕТЕ:
    "Найди информацию о Python"
    "Что такое машинное обучение?"
    "web_search python tutorial"

    📁 РАБОТА С ФАЙЛАМИ:
    "Покажи содержимое файла README.md"
    "Создай файл notes.txt с текстом 'Мои заметки'"
    "Покажи файлы в директории /home/user"
    "read_file config.json"
    "write_file todo.txt 'Купить молоко'"
    "list_directory ."

    🌐 HTTP ЗАПРОСЫ:
    "Сделай GET запрос на https://api.github.com/user"
    "http_request GET https://httpbin.org/get"

    💻 ТЕРМИНАЛЬНЫЕ КОМАНДЫ:
    "Выполни команду ls -la"
    "run_terminal_command pwd"
    "Показать текущую директорию"

    ПРИМЕРЫ РАЗГОВОРА:
    > Какая погода в Москве?
    > Цена биткоина в долларах
    > Найди последние новости о AI
    > Создай файл shopping.txt с покупками

    """
    print(help_text)


def setup_environment():
    """Настраивает окружение"""
    # Загружаем переменные окружения
    load_dotenv()

    # Проверяем наличие API ключа
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        print("❌ ОШИБКА: OPENAI_API_KEY не настроен!")
        print("\nНастройте API ключ в файле .env:")
        print("OPENAI_API_KEY=ваш_ключ_от_openai")
        print("\nПолучить ключ можно на: https://platform.openai.com/api-keys")
        sys.exit(1)


def interactive_mode(agent, use_langchain: bool = True):
    """Интерактивный режим работы с агентом"""
    print_banner()

    while True:
        try:
            # Получаем ввод пользователя
            user_input = input("\n👤 Вы: ").strip()

            if not user_input:
                continue

            # Обрабатываем специальные команды
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 До свидания!")
                break

            elif user_input.lower() == 'help':
                print_help()
                continue

            elif user_input.lower() == 'clear':
                agent.clear_memory()
                print("🧹 Память очищена")
                continue

            elif user_input.lower() == 'history':
                history = agent.get_conversation_history()
                if not history:
                    print("📝 История разговора пуста")
                else:
                    print("\n📝 ИСТОРИЯ РАЗГОВОРА:")
                    for i, msg in enumerate(history, 1):
                        role = "👤 Вы" if msg['role'] == 'user' else "🤖 Агент"
                        print(f"{i}. {role}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
                continue

            # Обрабатываем обычный запрос
            print("\n🤖 Агент думает...")

            if use_langchain:
                response = agent.process_query(user_input)
            else:
                response = agent.process_simple_query(user_input)

            print(f"\n🤖 Агент: {response}")

        except KeyboardInterrupt:
            print("\n\n👋 Прервано пользователем. До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {str(e)}")
            continue


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='AI Agent - Терминальный ассистент')
    parser.add_argument('--simple', action='store_true',
                       help='Использовать упрощенную версию агента (без LangChain)')
    parser.add_argument('--model', type=str, default=None,
                       help='Модель OpenAI для использования (переопределяет OPENAI_MODEL из .env)')
    parser.add_argument('--query', type=str,
                       help='Выполнить одиночный запрос и выйти')

    args = parser.parse_args()

    # Настраиваем окружение
    setup_environment()

    try:
        if args.simple:
            # Используем упрощенную версию
            agent = SimpleAgent()
            print("🚀 Запуск упрощенной версии агента...")
        else:
            # Используем полную версию с LangChain
            agent = AIAgent(model_name=args.model)
            model_name = args.model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
            print(f"🚀 Запуск агента с моделью {model_name}...")

        if args.query:
            # Одиночный запрос
            print(f"👤 Запрос: {args.query}")
            print("🤖 Агент думает...")

            if args.simple:
                response = agent.process_simple_query(args.query)
            else:
                response = agent.process_query(args.query)

            print(f"🤖 Ответ: {response}")
        else:
            # Интерактивный режим
            interactive_mode(agent, use_langchain=not args.simple)

    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
