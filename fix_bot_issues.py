#!/usr/bin/env python3
"""
Скрипт для исправления проблем с ботом
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def check_openai_quota():
    """Проверка квоты OpenAI API"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY не найден!")
        return False

    # Тестовый запрос к OpenAI
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-4o-mini',  # Используем более дешевую модель
        'messages': [
            {'role': 'user', 'content': 'test'}
        ],
        'max_tokens': 1
    }

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            print("✅ OpenAI API работает с моделью gpt-4o-mini")
            return True
        elif response.status_code == 429:
            error = response.json().get('error', {})
            print(f"❌ Превышена квота OpenAI: {error.get('message', 'Unknown error')}")
            print("\n⚠️  РЕШЕНИЕ:")
            print("1. Проверьте баланс на https://platform.openai.com/usage")
            print("2. Пополните баланс или дождитесь обновления квоты")
            print("3. Используйте более экономичную модель gpt-4o-mini (уже настроено)")
            return False
        else:
            print(f"❌ Ошибка OpenAI API: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке OpenAI: {e}")
        return False

def check_telegram_bot():
    """Проверка работы Telegram бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден!")
        return False

    try:
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe')

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Telegram бот работает: @{bot_info.get('username', 'unknown')}")

                # Проверяем Business аккаунт
                if bot_info.get('can_connect_to_business_account'):
                    print("✅ Поддержка Business аккаунтов включена")
                else:
                    print("⚠️  Business аккаунты могут не поддерживаться")

                return True

        print(f"❌ Ошибка Telegram API: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке Telegram: {e}")
        return False

def check_webhook():
    """Проверка webhook"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        return False

    try:
        response = requests.get(f'https://api.telegram.org/bot{token}/getWebhookInfo')

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook = data.get('result', {})
                url = webhook.get('url', '')

                if url:
                    print(f"✅ Webhook установлен: {url}")

                    pending = webhook.get('pending_update_count', 0)
                    if pending > 0:
                        print(f"⚠️  Есть {pending} необработанных обновлений")

                    last_error = webhook.get('last_error_message', '')
                    if last_error:
                        print(f"⚠️  Последняя ошибка: {last_error}")
                else:
                    print("❌ Webhook не установлен")

                return True

        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке webhook: {e}")
        return False

def check_railway_deployment():
    """Проверка деплоя на Railway"""
    try:
        # Проверяем переменные окружения Railway
        railway_env = os.getenv('RAILWAY_ENVIRONMENT')
        railway_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')

        if railway_env:
            print(f"✅ Railway среда: {railway_env}")

        if railway_url:
            print(f"✅ Railway URL: {railway_url}")

        # Проверяем доступность webhook URL
        webhook_url = "https://textilepro.up.railway.app/webhook"
        try:
            response = requests.get(webhook_url.replace('/webhook', '/health'), timeout=5)
            if response.status_code == 200:
                print(f"✅ Railway деплой доступен")
            else:
                print(f"⚠️  Railway деплой отвечает с кодом: {response.status_code}")
        except:
            print("⚠️  Railway деплой недоступен или нет health endpoint")

        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке Railway: {e}")
        return False

def main():
    print("=" * 50)
    print("🔍 ДИАГНОСТИКА TELEGRAM БОТА")
    print("=" * 50)

    # 1. Проверка Telegram бота
    print("\n1️⃣  Проверка Telegram бота:")
    check_telegram_bot()

    # 2. Проверка OpenAI
    print("\n2️⃣  Проверка OpenAI API:")
    check_openai_quota()

    # 3. Проверка Webhook
    print("\n3️⃣  Проверка Webhook:")
    check_webhook()

    # 4. Проверка Railway
    print("\n4️⃣  Проверка Railway деплоя:")
    check_railway_deployment()

    print("\n" + "=" * 50)
    print("📋 РЕКОМЕНДАЦИИ:")
    print("=" * 50)

    print("""
1. Если OpenAI квота превышена:
   - Проверьте баланс на https://platform.openai.com/usage
   - Пополните баланс или используйте другой API ключ
   - Модель уже изменена на gpt-4o-mini для экономии

2. Если Business API не работает:
   - Это нормально для некоторых типов сообщений
   - Бот должен автоматически использовать обычный API

3. Для проверки логов на Railway:
   railway logs --last 100

4. Для перезапуска бота на Railway:
   railway restart
    """)

if __name__ == "__main__":
    main()