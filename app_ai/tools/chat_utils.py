import gradio as gr
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import uuid
from pathlib import Path

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
def fetch_llm_answer(_, chat_id, chat_sessions):
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
        answer = f'Ошибка запроса: {e}'
        sources = []

    formatted = format_message('assistant', answer)
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

    chat_sessions[chat_id].append({'role': 'assistant', 'content': formatted})
    return chat_sessions[chat_id], chat_sessions

# --- Новый чат ---
def new_chat(chat_sessions, chat_titles):
    new_id = str(uuid.uuid4())
    if any(cid == new_id for _, cid in chat_titles):
        return new_id, chat_sessions, chat_titles, gr.update(choices=[t[0] for t in chat_titles])
    chat_sessions[new_id] = []
    title = f"Новый чат {len(chat_titles) + 1}"
    chat_titles.append((title, new_id))
    return new_id, chat_sessions, chat_titles, gr.update(choices=[t[0] for t in chat_titles], value=title)

# --- Переключение чата ---
def switch_chat(title, chat_titles, chat_sessions):
    for t, cid in chat_titles:
        if t == title:
            return cid, chat_sessions[cid] if cid in chat_sessions else []
    return gr.update(), []

# --- Переименование чата ---
def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip():
        return gr.update(), gr.update(), ""
    chat_titles = [(new_title if cid == current_chat_id else title, cid) for title, cid in chat_titles]
    return (
        chat_titles,
        gr.update(choices=[t[0] for t in chat_titles], value=new_title),
        ""
    )
