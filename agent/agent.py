import os
import json
import time
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from tools import ai_tools


class SimpleConversationMemory:
    """Простая реализация памяти для агента"""
    
    def __init__(self):
        self.chat_memory = ChatMessageHistory()
        self.memory_key = "chat_history"
        self.return_messages = True
    
    def save_context(self, inputs: dict, outputs: dict):
        """Сохраняет контекст в память"""
        if "input" in inputs:
            self.chat_memory.add_user_message(inputs["input"])
        if "output" in outputs:
            self.chat_memory.add_ai_message(outputs["output"])
    
    def load_memory_variables(self, inputs: dict):
        """Загружает переменные памяти"""
        return {self.memory_key: self.chat_memory.messages}
    
    def clear(self):
        """Очищает память"""
        self.chat_memory.clear()


class AIAgent:
    """Основной класс AI агента"""

    def __init__(self, model_name: str = None, temperature: float = None):
        # Загружаем переменные окружения
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        
        # Используем значения из .env или значения по умолчанию
        if model_name is None:
            model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        if temperature is None:
            temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

        # Инициализируем LLM
        llm_params = {
            "model_name": model_name,
            "temperature": temperature,
            "openai_api_key": api_key
        }
        
        # Добавляем base_url если указан
        if base_url:
            llm_params["openai_api_base"] = base_url
            
        self.llm = ChatOpenAI(**llm_params)
        self.tools = ai_tools

        # Создаем папку temp для сохранения файлов
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(script_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)

        # Загружаем память
        # Путь к memory.json в той же директории, где находится agent.py
        self.memory_file = os.path.join(script_dir, "memory.json")
        self.conversation_memory = self._load_memory()
        
        # Системный промпт для агента
        self.system_prompt = """Ты - AI ассистент с доступом к различным инструментам.

Доступные инструменты:
1. get_weather(city) - получить погоду в городе
2. get_crypto_price(coin, currency="usd") - получить цену криптовалюты
3. get_exchange_rate(from_currency, to_currency, amount=1.0) - курс обмена валют (USD, EUR, RUB и др.)
4. web_search(query, max_results=5) - поиск в интернете
5. http_request(method, url, headers=None, data=None, params=None) - HTTP запрос
6. read_file(file_path, max_lines=None) - прочитать файл
7. write_file(file_path, content, append=False) - записать в файл
8. list_directory(directory_path=".") - показать содержимое директории
9. run_terminal_command(command, cwd=None) - выполнить безопасную команду
10. generate_qr_code(data, filename="qr_code.png") - создать QR-код
11. add_reminder(text, date_time=None) - добавить напоминание
12. list_reminders(show_completed=False) - показать напоминания
13. delete_reminder(reminder_id) - удалить напоминание
14. calculate(expression) - математические вычисления

ВАЖНО: 
- Все файлы создаются и хранятся в папке "temp/". 
- При работе с файлами ВСЕГДА используй префикс "temp/" перед именем файла.
- Примеры: "temp/data.txt", "temp/output.json", "temp/qr.png"

ПРАВИЛА:
- Используй ТОЛЬКО ОДИН инструмент за раз
- После получения результата инструмента, НЕ вызывай другие инструменты
- Просто сформируй понятный ответ пользователю на основе результата

Для использования инструмента ответь СТРОГО в формате:
TOOL: имя_инструмента
ARGS: аргументы в JSON формате

Примеры:

Пользователь: "Какая погода в Москве?"
TOOL: get_weather
ARGS: {"city": "Москва"}

Пользователь: "Курс доллара к рублю"
TOOL: get_exchange_rate
ARGS: {"from_currency": "USD", "to_currency": "RUB"}

Пользователь: "Создай QR-код с текстом Hello"
TOOL: generate_qr_code
ARGS: {"data": "Hello", "filename": "hello_qr.png"}

Пользователь: "Напомни купить молоко"
TOOL: add_reminder
ARGS: {"text": "Купить молоко"}

Пользователь: "Посчитай 2^10 + sqrt(144)"
TOOL: calculate
ARGS: {"expression": "2**10 + sqrt(144)"}
"""

    def _load_memory(self) -> SimpleConversationMemory:
        """Загружает историю разговора из файла"""
        memory = SimpleConversationMemory()

        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    messages_data = json.load(f)

                for msg_data in messages_data:
                    if msg_data['type'] == 'human':
                        memory.chat_memory.add_user_message(msg_data['content'])
                    elif msg_data['type'] == 'ai':
                        memory.chat_memory.add_ai_message(msg_data['content'])

            except Exception as e:
                print(f"Ошибка загрузки памяти: {e}")

        return memory

    def _save_memory(self):
        """Сохраняет историю разговора в файл"""
        try:
            messages_data = []
            for msg in self.conversation_memory.chat_memory.messages:
                if isinstance(msg, HumanMessage):
                    messages_data.append({
                        'type': 'human',
                        'content': msg.content,
                        'timestamp': time.time()
                    })
                elif isinstance(msg, AIMessage):
                    messages_data.append({
                        'type': 'ai',
                        'content': msg.content,
                        'timestamp': time.time()
                    })

            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Ошибка сохранения памяти: {e}")

    def process_query(self, user_input: str) -> str:
        """
        Обрабатывает запрос пользователя и возвращает ответ

        Args:
            user_input: Запрос пользователя

        Returns:
            Ответ агента
        """
        try:
            # Добавляем запрос пользователя в память
            self.conversation_memory.chat_memory.add_user_message(user_input)
            
            # Формируем сообщения для LLM
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Добавляем историю из памяти (последние 10 сообщений)
            history = self.conversation_memory.chat_memory.messages[-10:]
            messages.extend(history)
            
            # Получаем ответ от LLM
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Проверяем, нужно ли вызвать инструмент (максимум 3 итерации)
            max_iterations = 3
            iteration = 0
            
            while "TOOL:" in response_text and iteration < max_iterations:
                iteration += 1
                print(f"\n[DEBUG] Обнаружен вызов инструмента в ответе LLM (итерация {iteration})")
                print(f"[DEBUG] Ответ LLM:\n{response_text}\n")
                
                # Парсим ответ
                tool_response = self._execute_tool_from_response(response_text)
                print(f"[DEBUG] Ответ инструмента: {tool_response}\n")
                
                # Отправляем результат инструмента обратно в LLM для формирования ответа
                messages.append(AIMessage(content=response_text))
                messages.append(HumanMessage(content=f"Результат выполнения: {tool_response}\n\nСформируй понятный ответ пользователю на основе этого результата. НЕ вызывай другие инструменты."))
                
                final_response = self.llm.invoke(messages)
                response_text = final_response.content
                print(f"[DEBUG] Ответ после инструмента: {response_text}\n")
            
            # Сохраняем ответ в память
            self.conversation_memory.chat_memory.add_ai_message(response_text)
            self._save_memory()
            
            return response_text

        except Exception as e:
            error_msg = f"Произошла ошибка при обработке запроса: {str(e)}"
            print(error_msg)
            
            self.conversation_memory.chat_memory.add_ai_message(error_msg)
            self._save_memory()
            
            return error_msg
    
    def _execute_tool_from_response(self, response_text: str) -> str:
        """Выполняет инструмент на основе ответа LLM"""
        try:
            # Парсим имя инструмента
            tool_match = re.search(r'TOOL:\s*(\w+)', response_text)
            if not tool_match:
                return "Не удалось определить инструмент"
            
            tool_name = tool_match.group(1)
            print(f"[DEBUG] Инструмент: {tool_name}")
            
            # Парсим аргументы - ищем JSON после ARGS:
            args_match = re.search(r'ARGS:\s*(\{.+?\})\s*$', response_text, re.MULTILINE | re.DOTALL)
            args = {}
            
            if args_match:
                args_str = args_match.group(1).strip()
                print(f"[DEBUG] Строка аргументов: {args_str[:200]}...")
                
                try:
                    # Пытаемся распарсить JSON
                    args = json.loads(args_str)
                    print(f"[DEBUG] Аргументы: {args}")
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] Ошибка парсинга JSON: {e}")
                    # Пытаемся исправить распространенные проблемы
                    try:
                        # Заменяем одинарные кавычки на двойные
                        args_str = args_str.replace("'", '"')
                        args = json.loads(args_str)
                        print(f"[DEBUG] Аргументы (после исправления): {args}")
                    except:
                        print(f"[DEBUG] Не удалось распарсить аргументы, используем пустой словарь")
                        args = {}
            
            # Вызываем соответствующий метод инструмента
            if hasattr(self.tools, tool_name):
                method = getattr(self.tools, tool_name)
                print(f"[DEBUG] Вызываем метод: {method}")
                
                # Вызываем метод напрямую
                if args:
                    result = method(**args)
                else:
                    # Если нет аргументов, показываем ошибку
                    return f"Не удалось извлечь аргументы для инструмента {tool_name}. Проверьте формат ARGS."
                    
                print(f"[DEBUG] Результат: {result}")
                return result
            else:
                return f"Инструмент '{tool_name}' не найден"
                
        except Exception as e:
            error_msg = f"Ошибка выполнения инструмента: {str(e)}"
            print(f"[DEBUG] {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Возвращает историю разговора"""
        history = []
        for msg in self.conversation_memory.chat_memory.messages:
            if isinstance(msg, HumanMessage):
                history.append({
                    'role': 'user',
                    'content': msg.content
                })
            elif isinstance(msg, AIMessage):
                history.append({
                    'role': 'assistant',
                    'content': msg.content
                })
        return history

    def clear_memory(self):
        """Очищает память разговора"""
        self.conversation_memory.clear()
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        print("Память очищена")


class SimpleAgent:
    """Упрощенная версия агента без LangChain для случаев, когда нужны простые ответы"""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

        llm_params = {
            "model_name": model_name,
            "temperature": temperature,
            "openai_api_key": api_key
        }
        
        # Добавляем base_url если указан
        if base_url:
            llm_params["openai_api_base"] = base_url
            
        self.llm = ChatOpenAI(**llm_params)

        # Загружаем инструменты напрямую
        from tools import ai_tools
        self.tools = ai_tools

    def process_simple_query(self, user_input: str) -> str:
        """
        Обрабатывает простой запрос, анализируя его и выбирая подходящий инструмент
        """
        try:
            # Создаем промпт для выбора инструмента
            system_prompt = """
            Ты - AI помощник. Проанализируй запрос пользователя и выбери наиболее подходящий инструмент.
            Доступные инструменты:

            1. get_weather - для запросов о погоде (например: "какая погода в Москве")
            2. get_crypto_price - для запросов о цене криптовалюты (например: "цена биткоина")
            3. web_search - для поиска информации в интернете
            4. http_request - для HTTP запросов к API
            5. read_file - для чтения файлов
            6. write_file - для записи в файлы
            7. list_directory - для просмотра содержимого директорий
            8. run_terminal_command - для выполнения безопасных команд терминала

            Если запрос не требует использования инструментов, просто ответь на него.

            Формат ответа:
            - Если нужен инструмент: "TOOL: имя_инструмента: параметры"
            - Если простой ответ: "ANSWER: твой ответ"
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]

            response = self.llm.invoke(messages)
            result = response.content.strip()

            # Обрабатываем ответ
            if result.startswith("TOOL:"):
                # Парсим вызов инструмента
                tool_call = result[5:].strip()
                return self._execute_tool_call(tool_call)

            elif result.startswith("ANSWER:"):
                return result[7:].strip()

            else:
                # Если формат не распознан, возвращаем как есть
                return result

        except Exception as e:
            return f"Ошибка обработки запроса: {str(e)}"

    def _execute_tool_call(self, tool_call: str) -> str:
        """Выполняет вызов инструмента"""
        try:
            # Парсим tool_call в формате "имя_инструмента: параметры"
            if ":" not in tool_call:
                return "Неверный формат вызова инструмента"

            tool_name, params_str = tool_call.split(":", 1)
            tool_name = tool_name.strip()
            params = params_str.strip()

            # Выполняем соответствующий инструмент
            if tool_name == "get_weather":
                return self.tools.get_weather(params)
            elif tool_name == "get_crypto_price":
                # Парсим параметры для крипты (coin, currency)
                if "," in params:
                    coin, currency = params.split(",", 1)
                    return self.tools.get_crypto_price(coin.strip(), currency.strip())
                else:
                    return self.tools.get_crypto_price(params)
            elif tool_name == "web_search":
                return self.tools.web_search(params)
            elif tool_name == "list_directory":
                if params:
                    return self.tools.list_directory(params)
                else:
                    return self.tools.list_directory()
            else:
                return f"Инструмент '{tool_name}' не реализован в простой версии"

        except Exception as e:
            return f"Ошибка выполнения инструмента: {str(e)}"
