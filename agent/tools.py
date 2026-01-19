import os
import json
import subprocess
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from geopy.geocoders import Nominatim
from duckduckgo_search import DDGS
import qrcode
from sympy import sympify, N


class AITools:
    """Класс для управления всеми инструментами AI агента"""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="ai_agent")
        self.safe_commands = {
            'ls', 'dir', 'pwd', 'echo', 'cat', 'head', 'tail',
            'grep', 'find', 'wc', 'sort', 'uniq', 'date', 'cal',
            'python', 'python3', 'pip', 'npm', 'git', 'docker'
        }

    def get_weather(self, city: str) -> str:
        """
        Получить текущую погоду для указанного города.

        Args:
            city: Название города

        Returns:
            Строка с информацией о погоде или ошибкой
        """
        try:
            # Получаем координаты города
            location = self.geolocator.geocode(city)
            if not location:
                return f"Не удалось найти город: {city}"

            lat, lon = location.latitude, location.longitude

            # Запрос к API погоды
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': True
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            weather = data['current_weather']

            temperature = weather['temperature']
            windspeed = weather['windspeed']
            weathercode = weather['weathercode']

            # Простая интерпретация weathercode
            weather_conditions = {
                0: "ясно",
                1: "преимущественно ясно",
                2: "переменная облачность",
                3: "пасмурно",
                45: "туман",
                48: "иней",
                51: "мелкий дождь",
                53: "умеренный дождь",
                55: "сильный дождь",
                61: "небольшой дождь",
                63: "дождь",
                65: "сильный дождь",
                71: "небольшой снег",
                73: "снег",
                75: "сильный снег",
                95: "гроза",
                96: "гроза с градом",
                99: "сильная гроза с градом"
            }

            condition = weather_conditions.get(weathercode, f"код погоды: {weathercode}")

            return f"Погода в {city}: {temperature}°C, ветер {windspeed} км/ч, {condition}"

        except Exception as e:
            return f"Ошибка при получении погоды: {str(e)}"

    def get_crypto_price(self, coin: str, currency: str = "usd") -> str:
        """
        Получить цену криптовалюты.

        Args:
            coin: Название криптовалюты (bitcoin, ethereum, etc.)
            currency: Валюта для отображения цены (usd, eur, rub)

        Returns:
            Строка с ценой криптовалюты или ошибкой
        """
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin.lower(),
                'vs_currencies': currency.lower()
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if coin.lower() not in data:
                return f"Криптовалюта '{coin}' не найдена. Попробуйте: bitcoin, ethereum, cardano, etc."

            price = data[coin.lower()][currency.lower()]
            return f"Цена {coin.capitalize()}: {price} {currency.upper()}"

        except Exception as e:
            return f"Ошибка при получении цены криптовалюты: {str(e)}"

    def web_search(self, query: str, max_results: int = 5) -> str:
        """
        Выполнить поиск в интернете с помощью DuckDuckGo.

        Args:
            query: Поисковый запрос
            max_results: Максимальное количество результатов

        Returns:
            Строка с результатами поиска
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return f"По запросу '{query}' ничего не найдено."

            response = f"Результаты поиска по запросу '{query}':\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result['title']}\n"
                response += f"   {result['body'][:200]}...\n"
                response += f"   URL: {result['href']}\n\n"

            return response.strip()

        except Exception as e:
            return f"Ошибка при поиске: {str(e)}"

    def http_request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                    data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, str]] = None) -> str:
        """
        Выполнить HTTP запрос.

        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            url: URL для запроса
            headers: Заголовки запроса
            data: Данные для тела запроса
            params: Query параметры

        Returns:
            Строка с ответом сервера или ошибкой
        """
        try:
            method = method.upper()
            if method not in ['GET', 'POST', 'PUT', 'DELETE']:
                return f"Неподдерживаемый HTTP метод: {method}"

            response = requests.request(
                method=method,
                url=url,
                headers=headers or {},
                json=data if data else None,
                params=params or {},
                timeout=30
            )

            result = f"HTTP {response.status_code}\n"
            result += f"Headers: {dict(response.headers)}\n\n"
            result += f"Response: {response.text[:1000]}"

            if len(response.text) > 1000:
                result += "... (обрезано)"

            return result

        except Exception as e:
            return f"Ошибка HTTP запроса: {str(e)}"

    def read_file(self, file_path: str, max_lines: Optional[int] = None) -> str:
        """
        Прочитать содержимое файла.

        Args:
            file_path: Путь к файлу
            max_lines: Максимальное количество строк для чтения

        Returns:
            Содержимое файла или ошибка
        """
        try:
            # Если путь относительный, делаем его относительно директории agent.py
            if not os.path.isabs(file_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                abs_path = os.path.join(script_dir, file_path)
            else:
                abs_path = file_path
            
            if not os.path.exists(abs_path):
                return f"Файл не найден: {abs_path}"

            with open(abs_path, 'r', encoding='utf-8') as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line.rstrip())
                    content = '\n'.join(lines)
                    if sum(1 for line in open(abs_path, 'r', encoding='utf-8')) > max_lines:
                        content += f"\n... (показано только {max_lines} строк)"
                else:
                    content = f.read()

            return f"Содержимое файла {abs_path}:\n{content}"

        except Exception as e:
            return f"Ошибка чтения файла: {str(e)}"

    def write_file(self, file_path: str, content: str, append: bool = False) -> str:
        """
        Записать содержимое в файл.

        Args:
            file_path: Путь к файлу
            content: Содержимое для записи
            append: True для добавления в конец файла, False для перезаписи

        Returns:
            Сообщение об успехе или ошибка
        """
        try:
            # Если путь относительный и не абсолютный, делаем его относительно директории agent.py
            if not os.path.isabs(file_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                abs_path = os.path.join(script_dir, file_path)
            else:
                abs_path = file_path
                
            print(f"[TOOL] Создание файла: {abs_path}")
            
            # Создаем родительские директории если их нет
            parent_dir = os.path.dirname(abs_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
                print(f"[TOOL] Директория создана: {parent_dir}")
            
            mode = 'a' if append else 'w'
            with open(abs_path, mode, encoding='utf-8') as f:
                f.write(content)

            action = "добавлено к" if append else "записано в"
            result = f"Содержимое успешно {action} файл {abs_path}"
            print(f"[TOOL] {result}")
            return result

        except Exception as e:
            error_msg = f"Ошибка записи в файл: {str(e)}"
            print(f"[TOOL] {error_msg}")
            return error_msg

    def list_directory(self, directory_path: str = ".") -> str:
        """
        Показать содержимое директории.

        Args:
            directory_path: Путь к директории

        Returns:
            Список файлов и папок или ошибка
        """
        try:
            if not os.path.exists(directory_path):
                return f"Директория не найдена: {directory_path}"

            if not os.path.isdir(directory_path):
                return f"Это не директория: {directory_path}"

            items = os.listdir(directory_path)
            if not items:
                return f"Директория {directory_path} пуста"

            files = []
            dirs = []

            for item in items:
                full_path = os.path.join(directory_path, item)
                if os.path.isdir(full_path):
                    dirs.append(f"[DIR] {item}")
                else:
                    files.append(f"[FILE] {item}")

            result = f"Содержимое директории {directory_path}:\n\n"
            if dirs:
                result += "Папки:\n" + "\n".join(dirs) + "\n\n"
            if files:
                result += "Файлы:\n" + "\n".join(files)

            return result.strip()

        except Exception as e:
            return f"Ошибка чтения директории: {str(e)}"

    def run_terminal_command(self, command: str, cwd: Optional[str] = None) -> str:
        """
        Выполнить безопасную терминальную команду.

        Args:
            command: Команда для выполнения
            cwd: Рабочая директория

        Returns:
            Вывод команды или ошибка
        """
        try:
            # Проверка безопасности команды
            first_word = command.split()[0] if command.split() else ""
            if first_word not in self.safe_commands:
                return f"Команда '{first_word}' не разрешена для безопасности. Разрешены только безопасные команды."

            # Запуск команды
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd
            )

            output = ""
            if result.stdout:
                output += f"Вывод:\n{result.stdout}"
            if result.stderr:
                output += f"Ошибки:\n{result.stderr}"

            if not output:
                output = "Команда выполнена без вывода"

            return f"Результат выполнения '{command}':\n{output}"

        except subprocess.TimeoutExpired:
            return f"Команда '{command}' превысила время ожидания (30 сек)"
        except Exception as e:
            return f"Ошибка выполнения команды: {str(e)}"

    def get_exchange_rate(self, from_currency: str, to_currency: str, amount: float = 1.0) -> str:
        """
        Получить курс обмена валют.

        Args:
            from_currency: Валюта источника (USD, EUR, RUB и т.д.)
            to_currency: Валюта назначения (USD, EUR, RUB и т.д.)
            amount: Сумма для конвертации (по умолчанию 1.0)

        Returns:
            Курс обмена и сконвертированная сумма
        """
        try:
            from_curr = from_currency.upper()
            to_curr = to_currency.upper()
            
            # Если одна из валют RUB - используем API ЦБ РФ
            if from_curr == 'RUB' or to_curr == 'RUB':
                return self._get_rate_cbr(from_curr, to_curr, amount)
            else:
                # Для остальных валют используем frankfurter.app
                return self._get_rate_frankfurter(from_curr, to_curr, amount)
            
        except Exception as e:
            return f"Ошибка получения курса валют: {str(e)}"
    
    def _get_rate_cbr(self, from_curr: str, to_curr: str, amount: float) -> str:
        """Получить курс через API ЦБ РФ (для RUB)"""
        try:
            # API ЦБ РФ - курсы к рублю
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            rates = data['Valute']
            
            # Маппинг кодов валют
            currency_map = {
                'USD': 'USD',
                'EUR': 'EUR',
                'GBP': 'GBP',
                'JPY': 'JPY',
                'CNY': 'CNY',
                'CHF': 'CHF',
                'TRY': 'TRY',
                'UAH': 'UAH',
                'KZT': 'KZT',
                'BYN': 'BYN'
            }
            
            if from_curr == 'RUB':
                # Из рублей в другую валюту
                if to_curr not in currency_map:
                    return f"Валюта {to_curr} не поддерживается ЦБ РФ"
                
                if to_curr not in rates:
                    return f"Курс для {to_curr} не найден"
                
                rate_data = rates[to_curr]
                # Курс: сколько рублей за единицу валюты
                rub_per_unit = rate_data['Value'] / rate_data['Nominal']
                # Обратный курс: сколько валюты за 1 рубль
                rate = 1 / rub_per_unit
                
            else:
                # Из другой валюты в рубли
                if from_curr not in currency_map:
                    return f"Валюта {from_curr} не поддерживается ЦБ РФ"
                
                if from_curr not in rates:
                    return f"Курс для {from_curr} не найден"
                
                rate_data = rates[from_curr]
                # Курс: сколько рублей за единицу валюты
                rate = rate_data['Value'] / rate_data['Nominal']
            
            converted = round(amount * rate, 2)
            date = data['Date'].split('T')[0]
            
            return (
                f"💱 Курс обмена (ЦБ РФ):\n"
                f"1 {from_curr} = {rate:.4f} {to_curr}\n\n"
                f"📊 Конвертация:\n"
                f"{amount} {from_curr} = {converted} {to_curr}\n\n"
                f"📅 Дата: {date}"
            )
            
        except Exception as e:
            return f"Ошибка получения курса через ЦБ РФ: {str(e)}"
    
    def _get_rate_frankfurter(self, from_curr: str, to_curr: str, amount: float) -> str:
        """Получить курс через frankfurter.app (без RUB)"""
        try:
            url = f"https://api.frankfurter.app/latest?from={from_curr}&to={to_curr}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if to_curr not in data.get('rates', {}):
                return f"Валюта {to_curr} не поддерживается"
            
            rate = data['rates'][to_curr]
            converted = round(amount * rate, 2)
            
            return (
                f"💱 Курс обмена:\n"
                f"1 {from_curr} = {rate:.4f} {to_curr}\n\n"
                f"📊 Конвертация:\n"
                f"{amount} {from_curr} = {converted} {to_curr}\n\n"
                f"📅 Дата: {data.get('date', 'N/A')}"
            )
            
        except Exception as e:
            return f"Ошибка получения курса: {str(e)}"

    def generate_qr_code(self, data: str, filename: str = "qr_code.png") -> str:
        """
        Сгенерировать QR-код.

        Args:
            data: Данные для кодирования (текст, URL и т.д.)
            filename: Имя файла для сохранения (по умолчанию qr_code.png)

        Returns:
            Сообщение об успехе или ошибка
        """
        try:
            # Если путь относительный, делаем его относительно директории agent.py
            if not os.path.isabs(filename):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # По умолчанию сохраняем QR коды в temp/
                if not filename.startswith('temp/'):
                    filename = f"temp/{filename}"
                abs_path = os.path.join(script_dir, filename)
            else:
                abs_path = filename
            
            # Создаем родительские директории если их нет
            parent_dir = os.path.dirname(abs_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Генерируем QR-код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(abs_path)
            
            return f"QR-код успешно создан: {abs_path}\nСодержимое: {data[:100]}{'...' if len(data) > 100 else ''}"
            
        except Exception as e:
            return f"Ошибка генерации QR-кода: {str(e)}"

    def add_reminder(self, text: str, date_time: str = None) -> str:
        """
        Добавить напоминание.

        Args:
            text: Текст напоминания
            date_time: Дата и время в формате "YYYY-MM-DD HH:MM" (опционально)

        Returns:
            Подтверждение добавления
        """
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            reminders_file = os.path.join(script_dir, "temp", "reminders.json")
            
            # Создаем папку temp если её нет
            os.makedirs(os.path.dirname(reminders_file), exist_ok=True)
            
            # Загружаем существующие напоминания
            if os.path.exists(reminders_file):
                with open(reminders_file, 'r', encoding='utf-8') as f:
                    reminders = json.load(f)
            else:
                reminders = []
            
            # Создаем новое напоминание
            reminder = {
                'id': len(reminders) + 1,
                'text': text,
                'date_time': date_time,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'completed': False
            }
            
            reminders.append(reminder)
            
            # Сохраняем
            with open(reminders_file, 'w', encoding='utf-8') as f:
                json.dump(reminders, f, ensure_ascii=False, indent=2)
            
            if date_time:
                return f"✅ Напоминание #{reminder['id']} добавлено на {date_time}:\n{text}"
            else:
                return f"✅ Напоминание #{reminder['id']} добавлено:\n{text}"
            
        except Exception as e:
            return f"Ошибка добавления напоминания: {str(e)}"

    def list_reminders(self, show_completed: bool = False) -> str:
        """
        Показать список напоминаний.

        Args:
            show_completed: Показать завершенные напоминания (по умолчанию False)

        Returns:
            Список напоминаний
        """
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            reminders_file = os.path.join(script_dir, "temp", "reminders.json")
            
            if not os.path.exists(reminders_file):
                return "📝 Напоминаний пока нет"
            
            with open(reminders_file, 'r', encoding='utf-8') as f:
                reminders = json.load(f)
            
            if not reminders:
                return "📝 Напоминаний пока нет"
            
            # Фильтруем напоминания
            if not show_completed:
                reminders = [r for r in reminders if not r.get('completed', False)]
            
            if not reminders:
                return "📝 Активных напоминаний нет"
            
            result = "📝 Список напоминаний:\n\n"
            for r in reminders:
                status = "✅" if r.get('completed') else "⏰"
                date_str = f" ({r['date_time']})" if r.get('date_time') else ""
                result += f"{status} #{r['id']}{date_str}: {r['text']}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"Ошибка чтения напоминаний: {str(e)}"

    def delete_reminder(self, reminder_id: int) -> str:
        """
        Удалить напоминание по ID.

        Args:
            reminder_id: ID напоминания

        Returns:
            Подтверждение удаления
        """
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            reminders_file = os.path.join(script_dir, "temp", "reminders.json")
            
            if not os.path.exists(reminders_file):
                return "Файл с напоминаниями не найден"
            
            with open(reminders_file, 'r', encoding='utf-8') as f:
                reminders = json.load(f)
            
            # Находим и удаляем напоминание
            original_count = len(reminders)
            reminders = [r for r in reminders if r['id'] != reminder_id]
            
            if len(reminders) == original_count:
                return f"Напоминание #{reminder_id} не найдено"
            
            # Сохраняем
            with open(reminders_file, 'w', encoding='utf-8') as f:
                json.dump(reminders, f, ensure_ascii=False, indent=2)
            
            return f"✅ Напоминание #{reminder_id} удалено"
            
        except Exception as e:
            return f"Ошибка удаления напоминания: {str(e)}"

    def calculate(self, expression: str) -> str:
        """
        Выполнить математические вычисления.

        Args:
            expression: Математическое выражение (поддерживает +, -, *, /, **, sqrt, sin, cos, и т.д.)

        Returns:
            Результат вычисления
        """
        try:
            # Используем sympy для безопасных вычислений
            result = sympify(expression)
            
            # Вычисляем численное значение
            numeric_result = N(result, 10)  # 10 знаков после запятой
            
            return f"Результат: {expression} = {numeric_result}"
            
        except Exception as e:
            return f"Ошибка вычисления '{expression}': {str(e)}\nПроверьте синтаксис выражения"


# Создаем экземпляр для использования
ai_tools = AITools()
