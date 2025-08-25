# 🚀 Инструкции по деплою бота

## ⚠️ ВАЖНО: Очистка старых сообщений

**ПРОБЛЕМА**: При каждом деплое Telegram отправляет все накопившиеся необработанные сообщения (pending updates), что приводит к лавине ответов на старые вопросы.

**РЕШЕНИЕ**: Обязательно очищайте pending updates перед каждым деплоем!

## 🧹 Как очистить старые сообщения

### Способ 1: Быстрая очистка (рекомендуется)
```bash
./clear_old_messages.sh
```

### Способ 2: Детальная очистка
```bash
python3 scripts/clear_pending_updates.py
```

## 📋 Полный процесс деплоя

### 1. Очистка старых сообщений
```bash
# Обязательно перед каждым деплоем!
./clear_old_messages.sh
```

### 2. Фиксация изменений
```bash
git add .
git commit -m "Описание изменений"
git push origin main
```

### 3. Мониторинг деплоя
```bash
# Следим за логами Railway
railway logs --service bot-production-472c
```

## 🛡️ Защита от старых сообщений

В коде бота добавлена автоматическая фильтрация:

- **Игнорируются** сообщения старше 5 минут
- **Логируется** возраст пропущенных сообщений
- **Обрабатываются** только актуальные сообщения и business_connection события

## 📊 Мониторинг

### Проверка pending updates
```bash
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" | jq '.result.pending_update_count'
```

### Проверка безопасности
```bash
python3 scripts/security_monitor.py
```

## 🚨 Что делать при проблемах

### Если бот отвечает на старые сообщения:
1. Немедленно запустите: `./clear_old_messages.sh`
2. Проверьте логи: `railway logs`
3. Убедитесь, что фильтрация по времени работает

### Если накопилось много pending updates:
```bash
# Проверяем количество
python3 -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()
r = requests.get(f'https://api.telegram.org/bot{os.getenv(\"TELEGRAM_BOT_TOKEN\")}/getWebhookInfo')
print(f'Pending: {r.json()[\"result\"][\"pending_update_count\"]}')
"

# Очищаем принудительно
python3 scripts/clear_pending_updates.py
```

## ✅ Чек-лист деплоя

- [ ] Запустил `./clear_old_messages.sh`
- [ ] Проверил, что pending_update_count = 0
- [ ] Зафиксировал изменения в Git
- [ ] Задеплоил на Railway
- [ ] Проверил логи на наличие ошибок
- [ ] Протестировал бота новым сообщением

## 📝 Заметки

- Скрипт очистки безопасен - он не удаляет данные, только очищает очередь Telegram
- Фильтрация по времени защищает от случайных накоплений
- Business connections всегда обрабатываются независимо от возраста
- Старые сообщения логируются для отладки

---

**ПОМНИТЕ**: Очистка перед деплоем - это не опция, а обязательная процедура!