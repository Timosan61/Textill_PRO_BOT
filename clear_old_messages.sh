#!/bin/bash
# 🧹 Быстрая очистка накопившихся сообщений перед деплоем

echo "🧹 Очистка старых сообщений перед деплоем..."
echo "========================================="

# Запускаем скрипт очистки
python3 scripts/clear_pending_updates.py

echo ""
echo "✅ Готово! Теперь можно безопасно деплоить бота"
echo "📝 Команды для деплоя:"
echo "   git add . && git commit -m 'Update' && git push"
echo "   railway logs --service bot-production-472c"