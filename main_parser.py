import os
import json
import requests
import sys
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, MessageMediaWebPage
from datetime import datetime, timedelta, timezone

# --- 1. КОНФИГУРАЦИЯ ---
try:
    API_ID = os.environ.get('API_ID')
    API_HASH = os.environ.get('API_HASH')
    N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

    if not all([API_ID, API_HASH, N8N_WEBHOOK_URL]):
        raise ValueError("Отсутствуют API_ID, API_HASH или N8N_WEBHOOK_URL в GitHub Secrets.")
    
    API_ID = int(API_ID)
    
except Exception as e:
    print(f"ОШИБКА КОНФИГУРАЦИИ: {e}")
    sys.exit(1)

CHANNELS_LIST = [
    '@bankrollo',
    '@BlackAudit',
    '@mvd_23',
]
SESSION_NAME = 'colab_session' 
BATCH_SIZE = 500
LIMIT_MESSAGES = 100

def clean_message(msg, channel_entity):
    """Преобразует объект сообщения Telethon в чистый словарь JSON."""
    if not msg or not msg.message:
        return None 

    channel_name = getattr(channel_entity, 'title', str(channel_entity))
    
    data = {
        'message_id': msg.id,
        'channel_id': msg.peer_id.channel_id if hasattr(msg.peer_id, 'channel_id') else None,
        'channel_name': channel_name,
        'text': msg.message,
        'date': msg.date.isoformat(),  # ISO-8601!
        'has_media': msg.media is not None,
        'media_type': None,
        'file_name': None
    }

    if msg.media:
        data['media_type'] = type(msg.media).__name__
        if isinstance(msg.media, MessageMediaDocument) and msg.media.document:
            for attr in msg.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    data['file_name'] = attr.file_name
                    break
        elif isinstance(msg.media, MessageMediaWebPage) and hasattr(msg.media.webpage, 'site_name'):
            data['file_name'] = msg.media.webpage.site_name

    return data

def send_to_webhook(batch):
    """Отправляет пакет сообщений в n8n."""
    if not batch:
        return

    print(f"Отправка пакета из {len(batch)} сообщений в n8n...")

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=batch, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        print(f"Пакет успешно отправлен. Статус: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке пакета в n8n: {e}")

def main():
    session_file = f'{SESSION_NAME}.session'
    
    if not os.path.exists(session_file):
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА: Файл сессии ({session_file}) не найден.")
        sys.exit(1)

    print(f"*** НАЧАЛО: ПОДКЛЮЧЕНИЕ ***")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        client.connect()
        if not client.is_user_authorized():
            print("!!! ОШИБКА АВТОРИЗАЦИИ: Сессионный файл недействителен или устарел.")
            sys.exit(1)

        print(f"Клиент авторизован. Начинаем парсинг {len(CHANNELS_LIST)} каналов...")

        for channel_identifier in CHANNELS_LIST:
            try:
                print(f"\n--- ПАРСИНГ КАНАЛА: {channel_identifier} ---")
                channel_entity = client.get_entity(channel_identifier)
                message_buffer = []
                messages = client.get_messages(channel_entity, limit=LIMIT_MESSAGES)
                
                print(f"Получено {len(messages)} сообщений. Обработка...")
                count_fresh = 0
                count_old = 0
                utc_now = datetime.now(timezone.utc)

                for msg in messages:
                    cleaned_data = clean_message(msg, channel_entity)
                    if cleaned_data:
                        # === ФИЛЬТРАЦИЯ: только за последние сутки ===
                        msg_time = msg.date
                        if msg_time.tzinfo is None:
                            msg_time = msg_time.replace(tzinfo=timezone.utc)
                        if msg_time >= utc_now - timedelta(days=1):
                            message_buffer.append(cleaned_data)
                            count_fresh += 1
                            if len(message_buffer) >= BATCH_SIZE:
                                send_to_webhook(message_buffer)
                                message_buffer = []
                        else:
                            count_old += 1

                # Отправка оставшихся
                if message_buffer:
                    send_to_webhook(message_buffer)

                print(f"Свежих сообщений: {count_fresh}, пропущено старых: {count_old}")
                print(f"Парсинг канала {channel_identifier} завершен.")

            except Exception as e:
                print(f"ОШИБКА ПАРСИНГА КАНАЛА {channel_identifier}: {e}. Пропускаем этот канал.")

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА TELETHON: {e}")
        
    finally:
        client.disconnect()
        print(f"\n*** КОНЕЦ: КЛИЕНТ TELETHON ОТКЛЮЧЕН. ***")

if __name__ == '__main__':
    main()
