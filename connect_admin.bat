@echo off
echo ====================================================
echo     Textil PRO Bot - SSH Tunnel для админ панели
echo ====================================================
echo.
echo 🔗 Создание SSH туннеля для Streamlit...
echo 📍 Сервер: 104.248.39.106
echo 🌐 После подключения откройте: http://localhost:8501
echo 🔐 Пароль для входа: password
echo.
echo ⚡ Подключение...
ssh -L 8501:localhost:8501 coder@104.248.39.106

pause