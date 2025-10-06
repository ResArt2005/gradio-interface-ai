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
    if new_id in chat_titles:
        return new_id, chat_sessions, chat_titles, gr.update(choices=list(chat_titles.values()))
    
    chat_sessions[new_id] = []
    title = f"Новый чат {len(chat_titles) + 1}"
    print("Создание чата: " + title)
    chat_titles[new_id] = title
    return new_id, chat_sessions, chat_titles, gr.update(choices=list(chat_titles.values()), value=title)

# --- Переключение чата ---
def switch_chat(title, chat_titles, chat_sessions):
    # Находим chat_id по title
    for chat_id, t in chat_titles.items():
        if t == title:
            print("Переключение чата: " + title)
            return chat_id, chat_sessions[chat_id] if chat_id in chat_sessions else []
    return gr.update(), []

# --- Переименование чата ---
def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip():
        return gr.update(), gr.update(), ""
    
    print("Переименование чата: " + new_title)
    chat_titles[current_chat_id] = new_title
    
    return (
        chat_titles,
        gr.update(choices=list(chat_titles.values()), value=new_title),
        ""
    )

# --- Синхронизация чатов ---
def sync_chat_list(chat_titles, current_chat_id):
    titles = list(chat_titles.values())
    if not titles:
        return gr.update(choices=[])
    
    active = chat_titles.get(current_chat_id)
    return gr.update(choices=titles, value=active)

# --- Добавление сообщения ---
def add_user_message(message, chat_id, chat_sessions, chat_titles):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []
    
    if chat_id not in chat_titles:
        title = f"Новый чат {len(chat_titles) + 1}"
        chat_titles[chat_id] = title

    user_msg = {"role": "user", "content": format_message("user", message)}
    chat_sessions[chat_id].append(user_msg)

    value = None
    if len(chat_sessions[chat_id]) == 1:
        short_title = " ".join(message.strip().split()[:4]) + ("..." if len(message.strip().split()) > 4 else "")
        chat_titles[chat_id] = short_title
        value = short_title

    choices = list(chat_titles.values())
    selected = value or chat_titles.get(chat_id)

    if selected not in choices:
        return gr.update(value="", autofocus=True), chat_sessions[chat_id], chat_sessions, chat_titles, gr.update(choices=choices)

    return gr.update(value="", autofocus=True), chat_sessions[chat_id], chat_sessions, chat_titles, gr.update(
        choices=choices, value=selected
    )

# --- Удаление чата ---
def delete_chat(current_chat_id, chat_sessions, chat_titles):
    """Удаляет текущий чат"""
    if not current_chat_id:
        print("Нет активного чата для удаления")
        return chat_sessions, chat_titles, gr.update()
    
    print(f"Удаление чата: {current_chat_id}")
    
    # Удаляем из сессий
    if current_chat_id in chat_sessions:
        del chat_sessions[current_chat_id]
    
    # Удаляем из заголовков
    if current_chat_id in chat_titles:
        del chat_titles[current_chat_id]
    
    # Выбираем новый текущий чат
    if chat_titles:
        # Берем последний chat_id и его title
        new_current_id = list(chat_titles.keys())[-1]
        new_choices = list(chat_titles.values())
        new_value = chat_titles[new_current_id]
    else:
        # Если чатов не осталось, создаем новый
        new_current_id = str(uuid.uuid4())
        chat_sessions[new_current_id] = []
        title = "Новый чат 1"
        chat_titles[new_current_id] = title
        new_choices = [title]
        new_value = title
    
    print(f"Новый текущий чат: {new_current_id}")
    
    return new_current_id, chat_sessions, chat_titles, gr.update(
        choices=new_choices, 
        value=new_value
    )