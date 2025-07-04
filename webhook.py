"""
🤖 Telegram Business Bot Webhook Server

Основной сервер для обработки сообщений через Telegram Business API.
Работает в режиме webhook для мгновенных ответов.

Возможности:
- Обработка обычных сообщений боту
- Обработка Business API сообщений (от вашего Premium аккаунта)
- AI-powered ответы через OpenAI
- Память диалогов через Zep
- Автоматическая установка webhook при старте
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
import telebot
import json
import asyncio
import requests

# Добавляем путь для импорта модулей бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Загрузка Telegram Business Bot Webhook Server...")

# Пытаемся импортировать AI agent
try:
    import bot
    print("✅ Модуль bot найден")
    from bot.agent import agent
    print("✅ AI Agent загружен успешно")
    AI_ENABLED = True
except ImportError as e:
    print(f"⚠️ AI Agent не доступен: {e}")
    print(f"📁 Текущая директория: {os.getcwd()}")
    print(f"📁 Файлы в директории: {os.listdir('.')}")
    if os.path.exists('bot'):
        print(f"📁 Файлы в bot/: {os.listdir('bot')}")
    AI_ENABLED = False
except Exception as e:
    print(f"❌ Ошибка загрузки AI Agent: {e}")
    AI_ENABLED = False

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "textil_pro_secret_2025")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN отсутствует!")

print(f"✅ Токен бота получен: {TELEGRAM_BOT_TOKEN[:20]}...")

# === СОЗДАНИЕ СИНХРОННОГО БОТА (НЕ ASYNC!) ===
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === ФУНКЦИЯ ДЛЯ BUSINESS API ===
def send_business_message(chat_id, text, business_connection_id):
    """
    Отправка сообщения через Business API используя прямой HTTP запрос
    (pyTelegramBotAPI не поддерживает business_connection_id)
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "business_connection_id": business_connection_id
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            logger.info(f"✅ Business API: сообщение отправлено через HTTP API")
            return result.get("result")
        else:
            logger.error(f"❌ Business API ошибка: {result}")
            return None
    except Exception as e:
        logger.error(f"❌ Business API HTTP ошибка: {e}")
        return None

# === FASTAPI ПРИЛОЖЕНИЕ ===
app = FastAPI(
    title="🤖 Telegram Business Bot", 
    description="Webhook-only режим для Telegram Business API"
)

# Хранилище последних updates для отладки
from collections import deque
last_updates = deque(maxlen=10)
update_counter = 0

@app.get("/")
async def health_check():
    """Health check endpoint"""
    try:
        bot_info = bot.get_me()
        return {
            "status": "🟢 ONLINE", 
            "service": "Telegram Business Bot Webhook",
            "bot": f"@{bot_info.username}",
            "bot_id": bot_info.id,
            "mode": "WEBHOOK_ONLY",
            "ai_status": "✅ ENABLED" if AI_ENABLED else "❌ DISABLED",
            "openai_configured": bool(os.getenv('OPENAI_API_KEY')),
            "endpoints": {
                "webhook_info": "/webhook/info",
                "set_webhook": "/webhook/set",
                "delete_webhook": "/webhook (DELETE method)"
            },
            "hint": "Используйте /webhook/set в браузере для установки webhook"
        }
    except Exception as e:
        return {"status": "🔴 ERROR", "error": str(e)}

@app.get("/webhook/info")
async def webhook_info():
    """Информация о webhook"""
    try:
        info = bot.get_webhook_info()
        return {
            "webhook_url": info.url or "❌ Не установлен",
            "pending_updates": info.pending_update_count,
            "last_error": info.last_error_message or "✅ Нет ошибок",
            "has_custom_certificate": info.has_custom_certificate,
            "allowed_updates": info.allowed_updates or ["все"]
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/webhook/set")
async def set_webhook_get():
    """Установка webhook через GET (для браузера)"""
    return await set_webhook()

@app.post("/webhook/set")
async def set_webhook():
    """Установка webhook"""
    try:
        webhook_url = "https://bot-production-472c.up.railway.app/webhook"
        
        result = bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET_TOKEN,
            allowed_updates=[
                "message",
                "business_connection", 
                "business_message",
                "edited_business_message",
                "deleted_business_messages"
            ]
        )
        
        if result:
            logger.info(f"✅ Webhook установлен: {webhook_url}")
            return {
                "status": "✅ SUCCESS",
                "webhook_url": webhook_url,
                "secret_token": "✅ Настроен",
                "allowed_updates": "✅ Business API включен"
            }
        else:
            return {"status": "❌ FAILED"}
            
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        return {"status": "❌ ERROR", "error": str(e)}

@app.delete("/webhook")
async def delete_webhook():
    """Удаление webhook"""
    try:
        result = bot.delete_webhook()
        return {"status": "✅ Webhook удален" if result else "❌ Ошибка"}
    except Exception as e:
        return {"status": "❌ ERROR", "error": str(e)}

@app.get("/debug/last-updates")
async def get_last_updates():
    """Показать последние полученные updates для отладки"""
    return {
        "total_received": update_counter,
        "last_10_updates": list(last_updates),
        "current_time": datetime.now().isoformat()
    }

@app.get("/debug/zep-status")
async def get_zep_status():
    """Проверить статус Zep Memory"""
    zep_info = {
        "zep_api_key_set": bool(os.getenv('ZEP_API_KEY')),
        "zep_api_key_length": len(os.getenv('ZEP_API_KEY', '')) if os.getenv('ZEP_API_KEY') else 0,
        "ai_agent_available": AI_ENABLED,
        "zep_client_initialized": False,
        "memory_mode": "unknown"
    }
    
    if AI_ENABLED:
        try:
            zep_info["zep_client_initialized"] = agent.zep_client is not None
            zep_info["memory_mode"] = "Zep Cloud" if agent.zep_client else "Local Fallback"
            zep_info["local_sessions_count"] = len(agent.user_sessions)
            zep_info["local_session_ids"] = list(agent.user_sessions.keys())
        except Exception as e:
            zep_info["error"] = str(e)
    
    return zep_info

@app.get("/debug/memory/{session_id}")
async def get_session_memory(session_id: str):
    """Получить память конкретной сессии"""
    if not AI_ENABLED:
        return {"error": "AI не включен"}
    
    try:
        memory_info = {
            "session_id": session_id,
            "zep_memory": None,
            "local_memory": None,
            "zep_available": agent.zep_client is not None
        }
        
        # Пробуем получить из Zep
        if agent.zep_client:
            try:
                context = await agent.get_zep_memory_context(session_id)
                messages = await agent.get_zep_recent_messages(session_id)
                memory_info["zep_memory"] = {
                    "context": context,
                    "recent_messages": messages
                }
            except Exception as e:
                memory_info["zep_error"] = str(e)
        
        # Получаем локальную память
        if session_id in agent.user_sessions:
            memory_info["local_memory"] = agent.user_sessions[session_id]
        
        return memory_info
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/test/business-send")
async def test_business_send(request: Request):
    """Тестовая отправка через Business API"""
    try:
        data = await request.json()
        chat_id = data.get("chat_id")
        connection_id = data.get("business_connection_id")
        text = data.get("text", "🧪 Тестовое сообщение Business API")
        
        if not chat_id:
            return {"error": "chat_id обязателен"}
        
        if connection_id:
            result = send_business_message(chat_id, text, connection_id)
            if result:
                return {"status": "✅ Отправлено через Business API", "connection_id": connection_id, "result": result}
            else:
                return {"status": "❌ Ошибка отправки через Business API"}
        else:
            bot.send_message(chat_id, text)
            return {"status": "✅ Отправлено как обычное сообщение"}
            
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.post("/webhook")
async def process_webhook(request: Request):
    """Главный обработчик webhook"""
    global update_counter
    try:
        # Проверяем secret token из заголовков
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_token != WEBHOOK_SECRET_TOKEN:
            logger.warning(f"❌ Неверный secret token: {secret_token}")
            return {"ok": False, "error": "Invalid secret token"}
        
        json_data = await request.body()
        json_string = json_data.decode('utf-8')
        
        logger.info(f"📨 Webhook получен: {json_string[:150]}...")
        print(f"📨 Обработка webhook update...")
        
        update_dict = json.loads(json_string)
        
        # Сохраняем update для отладки
        update_counter += 1
        debug_update = {
            "id": update_counter,
            "timestamp": datetime.now().isoformat(),
            "type": "unknown",
            "data": update_dict
        }
        
        # Определяем тип update
        if "message" in update_dict:
            debug_update["type"] = "message"
        elif "business_message" in update_dict:
            debug_update["type"] = "business_message"
        elif "business_connection" in update_dict:
            debug_update["type"] = "business_connection"
        elif "edited_business_message" in update_dict:
            debug_update["type"] = "edited_business_message"
        elif "deleted_business_messages" in update_dict:
            debug_update["type"] = "deleted_business_messages"
        else:
            debug_update["type"] = f"other: {list(update_dict.keys())}"
            
        last_updates.append(debug_update)
        logger.info(f"📊 Update #{update_counter} тип: {debug_update['type']}")
        
        # === ОБЫЧНЫЕ СООБЩЕНИЯ ===
        if "message" in update_dict:
            msg = update_dict["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            user_id = msg.get("from", {}).get("id", "unknown")
            user_name = msg.get("from", {}).get("first_name", "Пользователь")
            
            try:
                # Отправляем индикатор набора текста
                bot.send_chat_action(chat_id, 'typing')
                
                if text.startswith("/start"):
                    if AI_ENABLED:
                        response = agent.get_welcome_message()
                    else:
                        response = f"🤖 Привет, {user_name}! Я Textil PRO бот.\n\n✅ Работаю через webhook\n💼 Поддерживаю Business API\n\nНапишите ваш вопрос!"
                
                elif text.startswith("/help"):
                    response = """ℹ️ Помощь:
/start - начать работу
/help - показать помощь

Просто напишите ваш вопрос о текстильном производстве, и я с радостью помогу!

📞 Для срочных вопросов: +86 123 456 789"""
                
                elif text and AI_ENABLED:
                    # Используем AI для генерации ответа
                    try:
                        session_id = f"user_{user_id}"
                        # Создаем пользователя в Zep если нужно
                        if agent.zep_client:
                            await agent.ensure_user_exists(f"user_{user_id}", {
                                'first_name': user_name,
                                'email': f'{user_id}@telegram.user'
                            })
                            await agent.ensure_session_exists(session_id, f"user_{user_id}")
                        response = await agent.generate_response(text, session_id, user_name)
                    except Exception as ai_error:
                        logger.error(f"Ошибка AI генерации: {ai_error}")
                        response = f"Извините, произошла ошибка AI. Ваш вопрос: {text}\n\nПопробуйте позже или свяжитесь с поддержкой."
                    
                elif text:
                    # Fallback если AI не доступен
                    response = f"💬 {user_name}, получил ваш вопрос: {text}\n\n📞 Для детальной консультации свяжитесь с нашими специалистами."
                else:
                    response = "📎 Спасибо за файл! Я работаю только с текстовыми сообщениями."
                    
                # Отправляем без parse_mode для надежности
                bot.send_message(chat_id, response)
                logger.info(f"✅ Ответ отправлен в чат {chat_id}")
                print(f"✅ Отправлен ответ пользователю {user_name}")
                
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {e}")
                bot.send_message(chat_id, "Извините, произошла ошибка. Попробуйте позже.")
        
        # === BUSINESS СООБЩЕНИЯ ===
        elif "business_message" in update_dict:
            bus_msg = update_dict["business_message"]
            
            # Детальное логирование структуры business_message
            logger.info(f"📨 Business message полная структура: {json.dumps(bus_msg, ensure_ascii=False)[:500]}...")
            
            chat_id = bus_msg["chat"]["id"]
            text = bus_msg.get("text", "")
            user_id = bus_msg.get("from", {}).get("id", "unknown")
            business_connection_id = bus_msg.get("business_connection_id")
            user_name = bus_msg.get("from", {}).get("first_name", "Клиент")
            
            # Логируем business_connection_id для отладки
            logger.info(f"📊 Business message - connection_id: '{business_connection_id}' (тип: {type(business_connection_id)})")
            
            # Проверяем наличие business_connection_id
            if not business_connection_id:
                logger.warning(f"⚠️ Business message без connection_id от {user_name} ({user_id})")
            
            # Обрабатываем ВСЕ business сообщения с текстом
            if text:
                try:
                    logger.info(f"🔄 Начинаю обработку business message: text='{text}', chat_id={chat_id}")
                    bot.send_chat_action(chat_id, 'typing')
                    logger.info(f"✅ Отправлен typing индикатор")
                    
                    if AI_ENABLED:
                        # Используем AI для Business сообщений
                        logger.info(f"🤖 AI включен, генерирую ответ...")
                        session_id = f"business_{user_id}"
                        # Создаем пользователя в Zep если нужно
                        if agent.zep_client:
                            await agent.ensure_user_exists(f"business_{user_id}", {
                                'first_name': user_name,
                                'email': f'{user_id}@business.telegram.user'
                            })
                            await agent.ensure_session_exists(session_id, f"business_{user_id}")
                        response = await agent.generate_response(text, session_id, user_name)
                        logger.info(f"✅ AI ответ сгенерирован: {response[:100]}...")
                    else:
                        logger.info(f"🤖 AI отключен, использую стандартный ответ")
                        response = f"💼 Здравствуйте, {user_name}!\n\n✅ Ваше сообщение получено через Business API: {text}\n\n🤖 Наш специалист скоро ответит!"
                    
                    # Для business_message используем специальную функцию
                    logger.info(f"📤 Пытаюсь отправить ответ...")
                    if business_connection_id:
                        logger.info(f"📤 Отправляю через Business API с connection_id='{business_connection_id}'")
                        result = send_business_message(chat_id, response, business_connection_id)
                        if result:
                            logger.info(f"✅ Business ответ отправлен в чат {chat_id} с connection_id='{business_connection_id}'")
                        else:
                            logger.error(f"❌ Не удалось отправить через Business API")
                    else:
                        # Если connection_id отсутствует, логируем это как критическую ошибку
                        logger.error(f"❌ КРИТИЧНО: Получен business_message без connection_id! chat_id={chat_id}, user={user_name}")
                        # Пробуем отправить как обычное сообщение
                        bot.send_message(chat_id, response)
                        logger.warning(f"⚠️ Отправлено как обычное сообщение (fallback)")
                    
                    print(f"✅ Business ответ отправлен пользователю {user_name}")
                    
                except Exception as e:
                    # Детальное логирование ошибки с traceback
                    error_info = {
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "business_connection_id": business_connection_id,
                        "chat_id": chat_id,
                        "text": text
                    }
                    logger.error(f"❌ Ошибка обработки business сообщения: {e}")
                    logger.error(f"Traceback:\n{traceback.format_exc()}")
                    logger.error(f"Business connection_id: '{business_connection_id}'")
                    
                    # Сохраняем ошибку в debug данные
                    last_updates.append({
                        "id": f"error_{update_counter}",
                        "timestamp": datetime.now().isoformat(),
                        "type": "business_message_error",
                        "error_info": error_info
                    })
                    
                    # ВАЖНО: Отправляем ошибку ТОЖЕ через Business API!
                    try:
                        error_message = "Извините, произошла временная ошибка. Пожалуйста, попробуйте позже или обратитесь к нашему менеджеру."
                        
                        # Если есть business_connection_id - используем его
                        if business_connection_id:
                            result = send_business_message(chat_id, error_message, business_connection_id)
                            if result:
                                logger.info(f"✅ Сообщение об ошибке отправлено через Business API")
                            else:
                                # Если Business API не сработал, пробуем обычный способ
                                bot.send_message(chat_id, error_message)
                                logger.warning(f"⚠️ Business API не сработал, отправлено обычным способом")
                        else:
                            # Fallback: если нет connection_id, отправляем обычное сообщение
                            bot.send_message(chat_id, error_message)
                            logger.warning(f"⚠️ Сообщение об ошибке отправлено БЕЗ Business API (нет connection_id)")
                            
                    except Exception as send_error:
                        logger.error(f"❌ Не удалось отправить сообщение об ошибке: {send_error}")
        
        # === BUSINESS CONNECTION ===
        elif "business_connection" in update_dict:
            conn = update_dict["business_connection"]
            is_enabled = conn.get("is_enabled", False)
            user_name = conn.get("user", {}).get("first_name", "Пользователь")
            
            status = "✅ Подключен" if is_enabled else "❌ Отключен"
            logger.info(f"{status} к Business аккаунту: {user_name}")
        
        return {"ok": True, "status": "processed", "update_id": update_counter}
        
    except Exception as e:
        logger.error(f"❌ Ошибка webhook: {e}")
        return {"ok": False, "error": str(e)}

@app.on_event("startup")
async def startup():
    """Запуск сервера"""
    print("\n" + "="*50)
    print("🚀 TELEGRAM BUSINESS BOT WEBHOOK SERVER")
    print("="*50)
    
    # Очищаем webhook при старте
    try:
        bot.delete_webhook()
        print("🧹 Webhook очищен")
    except:
        pass
    
    try:
        bot_info = bot.get_me()
        print(f"🤖 Бот: @{bot_info.username}")
        print(f"📊 ID: {bot_info.id}")
        print(f"📛 Имя: {bot_info.first_name}")
        print("🔗 Режим: WEBHOOK ONLY")
        print("❌ Polling: ОТКЛЮЧЕН")
        print(f"🤖 AI: {'✅ ВКЛЮЧЕН' if AI_ENABLED else '❌ ОТКЛЮЧЕН'}")
        print(f"🔑 OpenAI API: {'✅ Настроен' if os.getenv('OPENAI_API_KEY') else '❌ Не настроен'}")
        print("="*50)
        logger.info("✅ Бот инициализирован успешно")
        
        # ВСЕГДА автоматически устанавливаем webhook при старте
        print("🔧 Автоматическая установка webhook...")
        try:
            # Сначала проверяем текущий статус
            current_webhook = bot.get_webhook_info()
            if current_webhook.url:
                print(f"📍 Текущий webhook: {current_webhook.url}")
            else:
                print("❌ Webhook не установлен")
            
            # Устанавливаем webhook
            webhook_url = os.getenv("WEBHOOK_URL", "https://bot-production-472c.up.railway.app/webhook")
            result = bot.set_webhook(
                url=webhook_url,
                secret_token=WEBHOOK_SECRET_TOKEN,
                allowed_updates=[
                    "message",
                    "business_connection", 
                    "business_message",
                    "edited_business_message",
                    "deleted_business_messages"
                ]
            )
            
            if result:
                print(f"✅ Webhook автоматически установлен: {webhook_url}")
                logger.info(f"✅ Webhook установлен при старте: {webhook_url}")
            else:
                print("❌ Не удалось установить webhook автоматически")
                logger.error("Ошибка автоматической установки webhook")
                
        except Exception as e:
            print(f"❌ Ошибка при автоматической установке webhook: {e}")
            logger.error(f"Ошибка автоустановки webhook: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        logger.error(f"❌ Ошибка инициализации бота: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Остановка сервера"""
    logger.info("🛑 Остановка Telegram Business Bot Webhook Server")
    print("🛑 Сервер остановлен")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🌐 Запуск на порту {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)