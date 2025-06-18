# 🚀 Быстрый запуск Streamlit админ панели

## Ваше текущее состояние
✅ Вы находитесь в правильной папке: `Textill_PRO_BOT`  
✅ У вас активно виртуальное окружение: `(venv)`

## 🎯 Простые шаги для запуска

### Шаг 1: Установка зависимостей
```bash
./quick_setup.sh
```

### Шаг 2: Запуск админ панели
```bash
python run_admin.py
```

### Шаг 3: Подключение с вашего компьютера
**На своем Windows компьютере** откройте PowerShell:
```powershell
ssh -L 8501:localhost:8501 coder@104.248.39.106
```

### Шаг 4: Открыть в браузере
http://localhost:8501  
**Пароль:** `password`

## 🔧 Если что-то не работает

### Проблема: Permission denied
```bash
sudo chmod +x quick_setup.sh
./quick_setup.sh
```

### Проблема: Streamlit не запускается
```bash
# Проверить установку
python -c "import streamlit; print('OK')"

# Переустановить
pip install --break-system-packages --force-reinstall streamlit
```

### Проблема: Порт занят
```bash
# Найти процесс на порту 8501
lsof -i :8501

# Убить процесс
kill -9 PID
```

## ⚡ Альтернативный запуск без SSH туннеля

Если SSH туннель не работает:
```bash
python run_admin_remote.py
```
Затем откройте: http://104.248.39.106:8501