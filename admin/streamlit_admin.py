import streamlit as st
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.config import INSTRUCTION_FILE, DEFAULT_INSTRUCTION, STREAMLIT_CONFIG
from admin.auth import check_password
from admin.deploy_integration import DeployManager, show_deploy_status


def load_instruction():
    try:
        with open(INSTRUCTION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        default_data = DEFAULT_INSTRUCTION.copy()
        default_data["last_updated"] = datetime.now().isoformat()
        return default_data


def save_instruction(instruction_data):
    try:
        instruction_data["last_updated"] = datetime.now().isoformat()
        with open(INSTRUCTION_FILE, 'w', encoding='utf-8') as f:
            json.dump(instruction_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False


def main():
    st.set_page_config(
        page_title=STREAMLIT_CONFIG['page_title'],
        page_icon=STREAMLIT_CONFIG['page_icon'],
        layout=STREAMLIT_CONFIG['layout']
    )
    
    # Проверка авторизации
    if not check_password():
        return
    
    # Заголовок  
    st.title("🤖 Textil PRO Bot - Админ панель")
    
    st.markdown("""
    **Как работает обновление:**
    1. 📝 Редактируете промпт в полях ниже
    2. 💾 Нажимаете "Сохранить" → файл обновляется в GitHub
    3. 🔄 Railway автоматически синхронизируется с GitHub (2-3 минуты)
    4. ⚡ Или используйте кнопку быстрого обновления для немедленного применения
    """)
    
    # Показываем статус деплоя в боковой панели
    deploy_manager = show_deploy_status()
    
    if not os.path.exists(INSTRUCTION_FILE):
        st.warning("⚠️ Файл инструкций не найден. Создайте новые инструкции.")
    
    instruction_data = load_instruction()
    
    system_instruction = st.text_area(
        "Системная инструкция:",
        value=instruction_data.get("system_instruction", ""),
        height=400
    )
    
    welcome_message = st.text_area(
        "Приветственное сообщение:",
        value=instruction_data.get("welcome_message", ""),
        height=150
    )
    
    st.markdown("---")
    
    # Статус текущего промпта в боте
    st.subheader("📊 Статус бота")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Проверить текущий промпт", use_container_width=True):
            try:
                import requests
                response = requests.get("https://bot-production-472c.up.railway.app/debug/prompt", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "error" not in data:
                        st.success("✅ Связь с ботом установлена")
                        st.json(data)
                    else:
                        st.error(f"❌ Ошибка бота: {data['error']}")
                else:
                    st.error(f"❌ HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ Не удается подключиться к боту: {e}")
    
    with col2:
        if st.button("🔄 Перезагрузить промпт", use_container_width=True):
            try:
                import requests
                response = requests.post("https://bot-production-472c.up.railway.app/admin/reload-prompt", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("changed"):
                        st.success(f"✅ Промпт обновлен: {data['old_updated']} → {data['new_updated']}")
                    else:
                        st.info("📝 Промпт перезагружен (без изменений)")
                else:
                    st.error(f"❌ HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ Ошибка перезагрузки: {e}")
    
    st.markdown("---")
    
    if st.button("🚀 Сохранить", type="primary", use_container_width=True):
        new_instruction_data = {
            "system_instruction": system_instruction,
            "welcome_message": welcome_message,
            "last_updated": datetime.now().isoformat()
        }
        
        if save_instruction(new_instruction_data):
            # Автоматический деплой через GitHub API
            commit_message = f"Update bot instructions via admin panel\n\n- Modified system instruction\n- Updated welcome message\n- Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
            
            # Конвертируем данные в JSON для передачи в GitHub API
            instruction_json = json.dumps(new_instruction_data, ensure_ascii=False, indent=2)
            
            deploy_manager.auto_deploy_changes(commit_message, instruction_json)
            st.balloons()
            
            # Добавляем кнопку для немедленной перезагрузки промпта
            st.markdown("### 🔄 Быстрое применение изменений")
            if st.button("⚡ Перезагрузить промпт в боте сейчас", type="secondary", use_container_width=True):
                try:
                    import requests
                    response = requests.post("https://bot-production-472c.up.railway.app/admin/reload-prompt", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("changed"):
                            st.success(f"✅ Промпт немедленно обновлен в боте!")
                            st.info(f"Старое время: {data['old_updated'][:16]}")
                            st.info(f"Новое время: {data['new_updated'][:16]}")
                        else:
                            st.info("📝 Промпт перезагружен (Railway еще не обновился)")
                            st.warning("⏳ Подождите 1-2 минуты и попробуйте еще раз")
                    else:
                        st.error(f"❌ HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Ошибка связи с ботом: {e}")
                    st.info("💡 Попробуйте через минуту, когда Railway обновится")


if __name__ == "__main__":
    main()