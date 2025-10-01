import os
import sys
from telethon.sync import TelegramClient

# --- КОНФИГУРАЦИЯ ---
try:
    # Обязательные переменные из GitHub Secrets
    API_ID_STR = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    
    # Переменные из INPUTS Workflow (читаем их из переменных среды)
    PHONE_NUMBER = os.getenv('INPUT_PHONE_NUMBER')
    AUTH_CODE = os.getenv('INPUT_AUTH_CODE')

    # ЖЕСТКАЯ ПРОВЕРКА ПЕРЕМЕННЫХ
    if not API_ID_STR or not API_HASH:
        raise ValueError("API_ID или API_HASH не найдены в SECRETS.")
    if not PHONE_NUMBER:
        raise ValueError("Номер телефона не передан (INPUT_PHONE_NUMBER).")
    
    API_ID = int(API_ID_STR)
    SESSION_NAME = 'auth_session_unique'
    SESSION_FILE = f'{SESSION_NAME}.session'
    
except Exception as e:
    print(f"ОШИБКА КОНФИГУРАЦИИ: {e}")
    sys.exit(1)


# --- ОСНОВНАЯ ЛОГИКА ---
if __name__ == '__main__':
    # Если код из INPUTS - это строка 'none', считаем его None
    if AUTH_CODE and AUTH_CODE.lower() == 'none':
        AUTH_CODE = None 
        
    client = None
    
    try:
        print(f"*** НАЧАЛО: АВТОРИЗАЦИЯ TELETHON ***")
        
        # Используем os.devnull для принудительного отключения интерактивности
        client = TelegramClient(
            SESSION_NAME, 
            API_ID, 
            API_HASH, 
            device_model='GitHub Actions Runner',
            system_version=os.devnull 
        )
        
        # Проверяем, существует ли сессия
        if not os.path.exists(SESSION_FILE):
            print("--- Сессионный файл не найден. Начинаем одноразовую авторизацию. ---")
            
            # КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Используем client.start(), который автоматически подключается, 
            # вместо client.connect()
            client.start()
            
            # А) ПЕРВЫЙ ЗАПУСК: Запрашиваем код
            if AUTH_CODE is None:
                print("Отправляем запрос на получение кода...")
                # Теперь мы точно подключены, и можем отправить запрос
                client.send_code_request(PHONE_NUMBER) 
                
                # Action завершается
                print("\n!!! ПЕРВЫЙ ЭТАП ЗАВЕРШЕН. СКОПИРУЙТЕ КОД ИЗ TELEGRAM И ЗАПУСТИТЕ ACTION ПОВТОРНО, ВВЕДЯ КОД В INPUTS. !!!")
                client.disconnect()
                sys.exit(0)
            
            # Б) ВТОРОЙ ЗАПУСК: Вводим код
            else:
                print(f"Попытка входа с кодом: {AUTH_CODE}")
                client.sign_in(PHONE_NUMBER, AUTH_CODE)
        
        # Проверяем авторизацию после всех попыток
        if client.is_user_authorized():
            print("--- АВТОРИЗАЦИЯ ПРОШЛА УСПЕШНО! ---")
            print("Теперь вы можете запускать основной скрипт main_parser.py. Файл сессии сохранен.")
        else:
            print("!!! АВТОРИЗАЦИЯ НЕ УДАЛАСЬ. ПРОВЕРЬТЕ КОД ИЛИ API_HASH.")
            
    except Exception as e:
        print(f"\n!!! КРИТИЧЕСКАЯ ОШИБКА ВЫПОЛНЕНИЯ: {e}")
        
    finally:
        if client and client.is_connected():
            client.disconnect()
            print("\n*** КОНЕЦ: КЛИЕНТ TELETHON ОТКЛЮЧЕН. ***")
