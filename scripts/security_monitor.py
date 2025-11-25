#!/usr/bin/env python3
"""
🔒 Security Monitor для Telegram Bot
Регулярно проверяет безопасность бота и уведомляет о проблемах
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
EXPECTED_WEBHOOK = "https://bot-production-472c.up.railway.app/webhook"
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')  # Ваш Telegram ID для уведомлений

def check_webhook_security():
    """Проверка webhook на взлом"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get('ok'):
            return {
                'status': 'ERROR',
                'message': 'Не удалось получить информацию о webhook'
            }
        
        webhook_info = data.get('result', {})
        current_webhook = webhook_info.get('url', '')
        
        # Проверяем webhook
        if not current_webhook:
            return {
                'status': 'WARNING',
                'message': 'Webhook не установлен!'
            }
        
        if current_webhook != EXPECTED_WEBHOOK:
            return {
                'status': 'CRITICAL',
                'message': f'⚠️ ВЗЛОМ! Webhook изменен на: {current_webhook}',
                'malicious_webhook': current_webhook,
                'ip_address': webhook_info.get('ip_address', 'Unknown')
            }
        
        # Проверяем ошибки
        last_error = webhook_info.get('last_error_message', '')
        if last_error:
            return {
                'status': 'WARNING', 
                'message': f'Ошибка webhook: {last_error}'
            }
        
        return {
            'status': 'OK',
            'message': 'Webhook безопасен',
            'webhook': current_webhook,
            'pending_updates': webhook_info.get('pending_update_count', 0)
        }
        
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': f'Ошибка проверки: {str(e)}'
        }

def send_alert(message):
    """Отправка уведомления админу"""
    if not ADMIN_CHAT_ID:
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': ADMIN_CHAT_ID,
        'text': f"🔒 Security Alert\n\n{message}",
        'parse_mode': 'HTML'
    }
    
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

def restore_webhook():
    """Автоматическое восстановление webhook при взломе"""
    # Удаляем вредоносный webhook
    delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    requests.get(delete_url, timeout=5)
    
    # Устанавливаем правильный webhook
    set_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {
        'url': EXPECTED_WEBHOOK,
        'secret_token': os.getenv('WEBHOOK_SECRET_TOKEN', 'textil_pro_business_secret_2025'),
        'allowed_updates': [
            "message",
            "business_connection",
            "business_message",
            "edited_business_message",
            "deleted_business_messages"
        ]
    }
    
    response = requests.post(set_url, json=data, timeout=10)
    return response.json()

def main():
    """Основная функция мониторинга"""
    print(f"\n🔒 Security Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Проверяем безопасность
    result = check_webhook_security()
    
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['status'] == 'CRITICAL':
        print("\n⚠️ ОБНАРУЖЕН ВЗЛОМ!")
        print(f"Вредоносный webhook: {result.get('malicious_webhook', 'Unknown')}")
        print(f"IP адрес злоумышленника: {result.get('ip_address', 'Unknown')}")
        
        # Отправляем уведомление
        alert_message = (
            f"<b>⚠️ БОТ ВЗЛОМАН!</b>\n\n"
            f"Webhook изменен на:\n<code>{result.get('malicious_webhook', '')}</code>\n"
            f"IP: <code>{result.get('ip_address', '')}</code>\n\n"
            f"Выполняется автоматическое восстановление..."
        )
        send_alert(alert_message)
        
        # Автоматически восстанавливаем
        print("\n🔧 Восстанавливаем webhook...")
        restore_result = restore_webhook()
        
        if restore_result.get('ok'):
            print("✅ Webhook восстановлен!")
            send_alert("✅ Webhook успешно восстановлен!")
        else:
            print("❌ Ошибка восстановления:", restore_result)
            send_alert(f"❌ Ошибка восстановления: {restore_result}")
    
    elif result['status'] == 'WARNING':
        print(f"\n⚠️ Предупреждение: {result['message']}")
        send_alert(f"⚠️ {result['message']}")
    
    elif result['status'] == 'OK':
        print(f"✅ Все в порядке!")
        print(f"Webhook: {result.get('webhook', '')}")
        print(f"Ожидающих обновлений: {result.get('pending_updates', 0)}")
    
    print("=" * 50)
    
    return 0 if result['status'] == 'OK' else 1

if __name__ == "__main__":
    sys.exit(main())