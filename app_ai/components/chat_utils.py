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

# --- Утилита для построения списка кортежей (label, value) ---
def build_choices(chat_titles: dict):
    return [(title, chat_id) for chat_id, title in chat_titles.items()]

# --- Новый чат ---
def new_chat(chat_sessions, chat_titles):
    new_id = str(uuid.uuid4())
    chat_sessions[new_id] = []

    # Уникальное название
    base_name = "Новый чат"
    i = 1
    existing_titles = set(chat_titles.values())
    while f"{base_name} {i}" in existing_titles:
        i += 1
    chat_titles[new_id] = f"{base_name} {i}"

    return new_id, chat_sessions, chat_titles, gr.update(
        choices=build_choices(chat_titles),
        value=new_id
    )

# --- Переключение чата ---
def switch_chat(chat_id, chat_titles, chat_sessions):
    if chat_id in chat_sessions:
        return chat_id, chat_sessions[chat_id]
    return gr.update(), []

# --- Переименование чата ---
def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip() or current_chat_id not in chat_titles:
        return gr.update(), gr.update(), ""
    
    chat_titles[current_chat_id] = new_title
    return (
    chat_titles,
    gr.update(choices=build_choices(chat_titles), value=current_chat_id, interactive=True),
    ""
    )


# --- Синхронизация списка чатов ---
def sync_chat_list(chat_titles, current_chat_id):
    if not chat_titles:
        return gr.update(choices=[])
    return gr.update(choices=build_choices(chat_titles), value=current_chat_id)

# --- Добавление сообщения ---
def add_user_message(message, chat_id, chat_sessions, chat_titles):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []

    user_msg = {"role": "user", "content": message}
    chat_sessions[chat_id].append(user_msg)

    return (
        gr.update(value="", autofocus=True),
        chat_sessions[chat_id],
        chat_sessions,
        chat_titles,
        gr.update(choices=build_choices(chat_titles), value=chat_id)
    )

# --- Удаление чата ---
def delete_chat(current_chat_id, chat_sessions, chat_titles):
    if not current_chat_id:
        return gr.update(), chat_sessions, chat_titles, gr.update()

    chat_sessions.pop(current_chat_id, None)
    chat_titles.pop(current_chat_id, None)

    new_current_id = next(reversed(chat_titles), None)

    return new_current_id, chat_sessions, chat_titles, gr.update(
        choices=build_choices(chat_titles),
        value=new_current_id
    )