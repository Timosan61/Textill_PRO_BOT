#!/bin/bash

echo "🚀 Настройка Streamlit админ панели для локального запуска"
echo "=================================================="

# Создаем виртуальное окружение
echo "📦 Создание виртуального окружения..."
python3 -m venv admin_env

# Активируем окружение
echo "⚡ Активация окружения..."
source admin_env/bin/activate

# Устанавливаем зависимости
echo "📥 Установка зависимостей..."
pip install --upgrade pip
pip install streamlit==1.28.1
pip install streamlit-ace==0.1.1
pip install gitpython==3.1.40
pip install requests==2.31.0

echo "✅ Установка завершена!"
echo ""
echo "🎯 Для запуска админ панели:"
echo "1. source admin_env/bin/activate"
echo "2. python run_admin_remote.py"
echo ""
echo "🌐 Затем откройте: http://localhost:8501"
echo "🔐 Пароль: password"