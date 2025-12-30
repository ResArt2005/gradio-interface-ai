from tools.dbpg.DB_chats import append_chat_log
from tools.dbpg.DB_messages import save_message
from tools.debug import logger
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os
FASTAPI_URL = "http://host.docker.internal:8000/query"

# --- Форматирование сообщений ---
def format_message(role, content):
    tz = os.getenv("TZ", "UTC")
    time_str = datetime.now(ZoneInfo(tz)).strftime("%H:%M:%S")
    name = "👤 **Пользователь**" if role == "user" else "🤖 **Ассистент**"
    return f"{name} [{time_str}]:\n\n{content}"

# --- Очистка чата ---
def clear_current_chat(chat_id, chat_sessions):
    if chat_sessions is None:
        chat_sessions = {}
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []
    return [], chat_sessions

# --- Получение ответа от LLM ---
def fetch_llm_answer(_, chat_id, chat_sessions, user_id=None, session_id=None):
    """
    Генерирует ответ (в тестовом виде или через FASTAPI), сохраняет ответ ассистента в БД,
    и возвращает обновлённую историю для chat_id и весь chat_sessions.
    Новая сигнатура: принимает user_id и session_id (опционально).
    """
    if chat_id not in chat_sessions:
        return [{"role": "assistant", "content": "Ошибка: Чат не найден."}], chat_sessions

    history = chat_sessions[chat_id]
    try:
        last_user_msg = history[-1]['content'].split(']:\n\n', 1)[-1]
        response = requests.post(FASTAPI_URL, json={'query': last_user_msg}, timeout=180)
        data = response.json()
        answer = data.get('answer', 'Ответ не получен')
        sources = data.get('sources', [])
    except Exception as e:
        last_user_msg = history[-1]['content'].split(']:\n\n', 1)[-1]
        answer = f'Тестовый ответ от LLM на сообщение "{last_user_msg}"'
        logger.info(answer)
        sources = []

    # Форматируем как раньше (оставляем HTML/детали)
    tz = os.getenv("TZ", "UTC")
    time_str = datetime.now(ZoneInfo(tz)).strftime("%H:%M:%S")
    formatted = f"🤖 **Ассистент** [{time_str}]:\n\n{answer}"
    if sources:
        formatted += '\n\n<details><summary>📎 <b>Источники</b></summary>\n\n'
        for i, src in enumerate(sources, 1):
            title = src.get('doc_title', 'Источник')
            page = src.get('page', '')
            snippet = src.get('snippet', '')
            url = src.get('url', '#')
            formatted += f'- <a href="{url}" target="_blank">{title}, стр. {page}</a>\n'
            formatted += f'  > {snippet.strip()}\n\n'
        formatted += '</details>'

    # Сохраняем ассистентское сообщение в память и в БД
    assistant_msg = {'role': 'assistant', 'content': formatted}
    chat_sessions[chat_id].append(assistant_msg)
    try:
        save_message(chat_id=chat_id, user_id=user_id, role='assistant', content=formatted, session_id=session_id)
    except Exception as e:
        logger.error(f"Failed to save assistant message to DB: {e}")
    append_chat_log(chat_id, {
        "event": "message",
        "role": "assistant",
        "chat_id": chat_id,
        "content": answer,
        "time": datetime.now().isoformat() # datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return chat_sessions[chat_id], chat_sessions