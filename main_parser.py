import os
import json
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# --- КОНСТАНТЫ И КОНФИГУРАЦИЯ ---
# Чтение ключей из переменных среды GitHub Actions
try:
    # API_ID и API_HASH должны быть установлены как переменные среды в GitHub Actions
    API_ID = int(os.getenv('API_ID'))
    API_HASH = os.getenv('API_HASH')
    # Имя файла сессии, который будет создан после успешной авторизации. 
    # Должно быть постоянным.
    SESSION_NAME = 'sochi_llm_session'
    
    if not API_ID or not API_HASH:
        raise ValueError("API_ID или API_HASH не найдены в переменных среды.")
        
except ValueError as e:
    print(f"ОШИБКА КОНФИГУРАЦИИ: {e}")
    exit(1)


# Список каналов для сбора данных. Используйте публичные имена (@...) или ID.
# Вы можете добавить сюда больше каналов для обучения
CHANNELS = [
    'sochi24tv', 
    'tipich_sochi', 
    # Добавьте свои каналы
]
# Количество сообщений для сбора из каждого канала за один запуск
LIMIT = 200

# Файл, куда будут сохраняться собранные данные в формате JSON Lines (JSONL)
OUTPUT_FILE = 'telegram_data_for_training.jsonl'


def collect_data(client, channels, limit):
    """Собирает сообщения из списка каналов."""
    all_messages = []
    
    for channel_id in channels:
        try:
            print(f"--> Начинаем сбор данных из канала: {channel_id}")
            
            # Получаем объект канала
            entity = client.get_entity(channel_id)
            
            # Получаем историю сообщений
            messages = client(GetHistoryRequest(
                peer=entity,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0,
            )).messages
            
            print(f"    Собрано {len(messages)} сообщений.")
            
            # Обрабатываем сообщения и форматируем их для обучения
            for message in messages:
                if message.message and message.id:
                    all_messages.append({
                        'id': message.id,
                        'channel': channel_id,
                        'date': str(message.date),
                        'text': message.message,
                        'views': message.views,
                    })

        except Exception as e:
            print(f"!!! Ошибка при обработке канала {channel_id}: {e}")
            continue

    return all_messages


def save_data(data, filename):
    """Сохраняет данные в формат JSONL (JSON Lines)."""
    print(f"\n--> Сохраняем {len(data)} сообщений в файл {filename}")
    with open(filename, 'a', encoding='utf-8') as f:
        for record in data:
            # Используем ensure_ascii=False для корректного сохранения кириллицы
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print("Сохранение завершено.")


# --- ОСНОВНАЯ ЛОГИКА ---
if __name__ == '__main__':
    client = None
    try:
        print(f"*** НАЧАЛО: ПОДГОТОВКА К АВТОРИЗАЦИИ TELETHON ***")
        
        # 1. СОЗДАНИЕ КЛИЕНТА
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        # client.start() выполняет интерактивную авторизацию.
        # Action приостановит выполнение, ожидая ввод (Phone, Code, Password).
        client.start() 

        if client.is_user_authorized():
            print("--- АВТОРИЗАЦИЯ ПРОШЛА УСПЕШНО! ---")
            
            # 2. СБОР ДАННЫХ
            scraped_data = collect_data(client, CHANNELS, LIMIT)
            
            # 3. СОХРАНЕНИЕ
            if scraped_data:
                save_data(scraped_data, OUTPUT_FILE)
            else:
                print("Сбор данных завершен, но сообщений не найдено.")
                
        else:
            # Это сообщение будет выведено, если Action остановится в ожидании ввода.
            print("!!! АВТОРИЗАЦИЯ НЕ ЗАВЕРШЕНА. ПОЖАЛУЙСТА, ВВЕДИТЕ ДАННЫЕ В ЛОГАХ ПРИ ВЫПОЛНЕНИИ.")
            
    except Exception as e:
        print(f"\n!!! КРИТИЧЕСКАЯ ОШИБКА ВЫПОЛНЕНИЯ: {e}")
        
    finally:
        # Обязательное отключение клиента
        if client and client.is_connected():
            client.disconnect()
            print("\n*** КОНЕЦ: КЛИЕНТ TELETHON ОТКЛЮЧЕН. ***")
