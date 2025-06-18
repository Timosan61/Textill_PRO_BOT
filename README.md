# 🤖 Textil PRO Support Bot

Умный Telegram бот для службы поддержки компании Textile Pro. Консультант "Анастасия" автоматически отвечает на вопросы о производстве одежды в Китае, Индии и Бангладеш с использованием AI технологий.

## ✨ Ключевые возможности

🧠 **Умный AI консультант "Анастасия"**
- Персонализированные ответы на основе базы знаний компании
- Контекстное понимание диалога с сохранением истории
- Автоматическое перенаправление к менеджерам при необходимости

🚀 **Современные технологии**
- OpenAI GPT-4o для генерации естественных ответов
- Zep Cloud для долгосрочной памяти разговоров
- Асинхронная архитектура для высокой производительности

⚙️ **Полная автоматизация деплоя**
- GitOps workflow с автоматическими обновлениями
- Portainer API для удаленного управления
- Claude Code интеграция для голосового управления

## 🛠️ Технологический стек

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| **Backend** | Python 3.12 + AsyncTeleBot | Асинхронная обработка сообщений |
| **AI Engine** | OpenAI GPT-4o | Генерация умных ответов |
| **Memory** | Zep Cloud | Сохранение контекста диалогов |
| **Deployment** | Docker + Portainer | Контейнеризация и управление |
| **Infrastructure** | DockerHosting.ru VPS | Надежный хостинг |

## ⚡ Быстрое развертывание

### Вариант 1: Автоматический деплой (рекомендуется)
```bash
# Создание стека через Portainer API
python portainer_deploy.py create

# Проверка статуса
python claude_commands.py status
```

### Вариант 2: Локальная разработка
```bash
# 1. Настройка окружения
cp .env.example .env
# Заполните переменные в .env

# 2. Запуск через Docker
docker-compose up -d

# 3. Мониторинг
docker-compose logs -f
```

### Вариант 3: Ручной деплой на VPS
```bash
# Клонирование на сервер
git clone https://github.com/YOUR_USERNAME/textil-pro-bot.git
cd textil-pro-bot

# Настройка и запуск
cp .env.example .env
# Отредактируйте .env
docker-compose up -d
```

## 🎛️ Управление и мониторинг

### 🗣️ Голосовые команды для Claude Code
```bash
"обнови бота"     → python claude_commands.py deploy
"проверь статус"  → python claude_commands.py status
"покажи логи"     → python claude_commands.py logs
"перезапусти"     → python claude_commands.py restart
```

### 🔧 API команды Portainer
```bash
python portainer_deploy.py create   # Создать новый стек
python portainer_deploy.py update   # Обновить из Git
python portainer_deploy.py status   # Проверить статус
python portainer_deploy.py logs     # Просмотр логов
python portainer_deploy.py restart  # Перезапуск сервисов
```

### 📱 Команды Telegram бота
| Команда | Описание | Доступ |
|---------|----------|---------|
| `/start` | Начать работу с ботом | Все пользователи |
| `/help` | Показать справку | Все пользователи |
| `/reload` | Перезагрузить инструкции | Администраторы |

## 📁 Архитектура проекта

```
textil-pro-bot/
├── 🤖 bot/                    # Основной код бота
│   ├── main.py               # Точка входа приложения
│   ├── handlers.py           # Обработчики Telegram событий
│   ├── agent.py              # AI агент "Анастасия"
│   └── config.py             # Конфигурация и переменные
├── 📊 data/                   # Данные и настройки
│   └── instruction.json      # База знаний для AI
├── 🎛️ admin/                  # Панель администратора
│   └── streamlit_admin.py    # Веб-интерфейс управления
├── 🐳 Docker файлы           # Контейнеризация
│   ├── docker-compose.yaml  # Оркестрация сервисов
│   └── Dockerfile           # Образ приложения
├── ⚙️ Автоматизация          # Деплой и управление
│   ├── portainer_deploy.py  # Portainer API клиент
│   └── claude_commands.py   # Claude Code интеграция
└── 📚 Документация          # Инструкции и описания
    ├── README.md            # Основная документация
    └── PORTAINER_SETUP_GUIDE.md  # Руководство по настройке
```

## 🔐 Конфигурация окружения

### Обязательные переменные
| Переменная | Назначение | Пример |
|------------|------------|---------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather | `123456:ABC...` |
| `OPENAI_API_KEY` | Ключ OpenAI API | `sk-proj-...` |
| `ZEP_API_KEY` | Ключ Zep Memory Cloud | `z_...` |

### Опциональные переменные
| Переменная | Назначение | По умолчанию |
|------------|------------|--------------|
| `BOT_USERNAME` | Имя пользователя бота | `@textilprofi_bot` |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-4o` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

## 🚀 Автоматизация деплоя

### 🔄 GitOps Workflow
1. **Изменение кода** → `git push`
2. **Webhook уведомление** → Portainer
3. **Автоматическая пересборка** → Docker
4. **Перезапуск сервисов** → Без простоя

### 🎯 One-Click операции
```bash
# Единая команда для полного обновления
python claude_commands.py deploy

# Быстрая диагностика
python claude_commands.py status

# Мониторинг в реальном времени
python claude_commands.py logs
```

## 📞 Поддержка

- **Telegram менеджер**: https://t.me/textilepro_manager
- **Сайт**: https://textilprofi.ru

---

**Бот разработан с использованием Claude Code для автоматизации текстильного производства** 🤖