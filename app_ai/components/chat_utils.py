import gradio as gr
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import uuid
from pathlib import Path
from tools.debug import logger
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

    logger.success(f"создан новый чат {chat_titles[new_id]} {new_id}")

    return new_id, chat_sessions, chat_titles, gr.update(
        choices=build_choices(chat_titles),
        value=new_id
    )

# --- Переключение чата ---
def switch_chat(chat_id, chat_titles, chat_sessions):
    if chat_id in chat_sessions:
        logger.success(f"Переключение на чат {chat_titles[chat_id]} {chat_id}")
        return chat_id, chat_sessions[chat_id]
    logger.error(f"Чат с ID {chat_id} не найден!")
    return gr.update(), []

# --- Переименование чата ---
def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip() or current_chat_id not in chat_titles:
        return gr.update(), gr.update(), ""
    logger.success(f"Чат {chat_titles[current_chat_id]} {current_chat_id} переименован в {new_title}")
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

    logger.info(f"Сообщение от пользователя {message}")
    logger.info(f"Текущий чат {chat_titles[chat_id]} {chat_id}")

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
    
    logger.success(f"Чат успешно {chat_titles[current_chat_id]} {current_chat_id} удалён.")

    chat_sessions.pop(current_chat_id, None)
    chat_titles.pop(current_chat_id, None) # Новый текущий чат: последний в словаре
    new_current_id = next(iter(chat_titles), None)
    
    logger.info(f"Переключение на чат {chat_titles[new_current_id]} {new_current_id}.")

    return new_current_id, chat_sessions, chat_titles, gr.update(
        choices=build_choices(chat_titles),
        value=new_current_id
        )