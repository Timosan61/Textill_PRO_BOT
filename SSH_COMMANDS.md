# 🚀 SSH команды для доступа к Streamlit админ панели

## 📍 IP адрес вашего сервера: `104.248.39.106`

## ✅ Правильные команды подключения

### Для Windows (PowerShell/CMD):
```bash
ssh -L 8501:localhost:8501 coder@104.248.39.106
```

### Для Linux/Mac:
```bash
ssh -L 8501:localhost:8501 coder@104.248.39.106
```

### С указанием порта (если SSH не на стандартном порту):
```bash
ssh -p 22 -L 8501:localhost:8501 coder@104.248.39.106
```

## 🎯 Пошаговая инструкция

### Шаг 1: Создание SSH туннеля
На вашем **локальном** компьютере (Windows) откройте PowerShell и выполните:
```powershell
ssh -L 8501:localhost:8501 coder@104.248.39.106
```

### Шаг 2: Запуск админ панели на сервере
В VS Code (на сервере) выполните:
```bash
# Первый раз - установка зависимостей
./local_setup.sh

# Активация окружения
source admin_env/bin/activate

# Запуск админ панели
python run_admin.py
```

### Шаг 3: Открытие в браузере
Откройте в браузере: **http://localhost:8501**
Пароль: **password**

## 🔧 Альтернативные способы

### Способ 1: Прямой доступ (без SSH туннеля)
На сервере запустите:
```bash
source admin_env/bin/activate
python run_admin_remote.py
```
Затем откройте: **http://104.248.39.106:8501**

### Способ 2: VS Code Port Forwarding
1. В VS Code нажмите `Ctrl+Shift+P`
2. Найдите "Ports: Focus on Ports View"
3. Добавьте порт `8501`
4. Запустите `python run_admin.py`
5. VS Code автоматически создаст ссылку

## 🚨 Troubleshooting

### Ошибка "Connection refused"
```bash
# Проверьте, что Streamlit запущен
ps aux | grep streamlit

# Проверьте порт
netstat -tlnp | grep 8501
```

### SSH ключи
Если требуется SSH ключ:
```bash
ssh -i ~/.ssh/your_key -L 8501:localhost:8501 coder@104.248.39.106
```

### Firewall
Если не работает прямой доступ, проверьте firewall:
```bash
sudo ufw status
sudo ufw allow 8501
```

## 📁 Готовый батник для Windows

Скачайте файл `connect_admin.bat` и запустите его двойным кликом.
Он автоматически создаст SSH туннель с правильными параметрами.