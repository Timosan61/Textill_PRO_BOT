#!/usr/bin/env python3
"""
🔧 Очистка накопившихся pending updates в Telegram Bot API
Запускать перед каждым деплоем для предотвращения лавины старых сообщений
"""

import os
import requests
import json
from datetime import datetime
import sys

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    sys.exit(1)

def get_webhook_info():
    """Получение информации о webhook и pending updates"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            webhook_info = data.get('result', {})
            return {
                'url': webhook_info.get('url', ''),
                'pending_update_count': webhook_info.get('pending_update_count', 0),
                'last_error_date': webhook_info.get('last_error_date'),
                'last_error_message': webhook_info.get('last_error_message', '')
            }
        else:
            return {'error': data.get('description', 'Unknown error')}
            
    except Exception as e:
        return {'error': str(e)}

def clear_pending_updates():
    """Очистка всех pending updates через deleteWebhook + setWebhook"""
    print("🧹 Очистка накопившихся pending updates...")
    
    # Получаем текущую информацию о webhook
    webhook_info = get_webhook_info()
    
    if 'error' in webhook_info:
        print(f"❌ Ошибка получения webhook info: {webhook_info['error']}")
        return False
    
    current_url = webhook_info.get('url', '')
    pending_count = webhook_info.get('pending_update_count', 0)
    
    print(f"📊 Текущая информация:")
    print(f"   Webhook URL: {current_url}")
    print(f"   Pending updates: {pending_count}")
    
    if pending_count == 0:
        print("✅ Нет накопившихся обновлений для очистки")
        return True
    
    print(f"⚠️  Найдено {pending_count} необработанных обновлений")
    print("🔄 Выполняю очистку...")
    
    try:
        # Шаг 1: Удаляем webhook (это очистит pending updates)
        delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        delete_data = {
            'drop_pending_updates': True  # КЛЮЧЕВОЙ ПАРАМЕТР для очистки!
        }
        
        delete_response = requests.post(delete_url, json=delete_data, timeout=10)
        delete_result = delete_response.json()
        
        if not delete_result.get('ok'):
            print(f"❌ Ошибка удаления webhook: {delete_result}")
            return False
            
        print("✅ Webhook удален, pending updates очищены")
        
        # Шаг 2: Восстанавливаем webhook (если был установлен)
        if current_url:
            print(f"🔄 Восстанавливаем webhook: {current_url}")
            
            set_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            set_data = {
                'url': current_url,
                'secret_token': os.getenv('WEBHOOK_SECRET_TOKEN', 'textil_pro_business_secret_2025'),
                'allowed_updates': [
                    "message",
                    "business_connection",
                    "business_message", 
                    "edited_business_message",
                    "deleted_business_messages"
                ]
            }
            
            set_response = requests.post(set_url, json=set_data, timeout=10)
            set_result = set_response.json()
            
            if set_result.get('ok'):
                print("✅ Webhook восстановлен")
                
                # Проверяем результат
                new_info = get_webhook_info()
                if 'error' not in new_info:
                    print(f"📊 Результат очистки:")
                    print(f"   Pending updates: {new_info.get('pending_update_count', 0)}")
                    
                return True
            else:
                print(f"❌ Ошибка восстановления webhook: {set_result}")
                return False
        else:
            print("ℹ️  Webhook не был установлен, восстановление не требуется")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        return False

def main():
    """Основная функция"""
    print(f"\n🧹 Очистка Pending Updates - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Получаем информацию о webhook до очистки
    print("📊 Проверяем текущее состояние...")
    webhook_info = get_webhook_info()
    
    if 'error' in webhook_info:
        print(f"❌ Не удалось получить информацию о webhook: {webhook_info['error']}")
        return 1
    
    pending_count = webhook_info.get('pending_update_count', 0)
    
    if pending_count == 0:
        print("✅ Накопившихся обновлений нет - очистка не требуется")
        return 0
    
    print(f"⚠️  Обнаружено {pending_count} накопившихся обновлений")
    print("🚀 Запускаю процедуру очистки...")
    
    # Выполняем очистку
    success = clear_pending_updates()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ОЧИСТКА ЗАВЕРШЕНА УСПЕШНО")
        print("✅ Бот готов к обработке только новых сообщений")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ ОШИБКА ОЧИСТКИ")
        print("❌ Проверьте токен и доступность Telegram API")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())