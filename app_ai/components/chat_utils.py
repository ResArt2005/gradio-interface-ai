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
    print("Создание чата: " + title)
    chat_titles.append((title, new_id))
    return new_id, chat_sessions, chat_titles, gr.update(choices=[t[0] for t in chat_titles], value=title)

# --- Переключение чата ---
def switch_chat(title, chat_titles, chat_sessions):
    for t, cid in chat_titles:
        if t == title:
            print("Переключение чата: " + title)
            return cid, chat_sessions[cid] if cid in chat_sessions else []
    return gr.update(), []

# --- Переименование чата ---
def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip():
        return gr.update(), gr.update(), ""
    print("Переименование чата: " + new_title)
    chat_titles = [(new_title if cid == current_chat_id else title, cid) for title, cid in chat_titles]
    return (
        chat_titles,
        gr.update(choices=[t[0] for t in chat_titles], value=new_title),
        ""
    )

# --- Синхронизация чатов ---
def sync_chat_list(chat_titles, current_chat_id):
    titles = [t for t, _ in chat_titles]
    active = next((t for t, cid in chat_titles if cid == current_chat_id), None)
    if not titles:
        return gr.update(choices=[])
    return gr.update(choices=titles, value=active)

# --- Добавление сообщения ---
def add_user_message(message, chat_id, chat_sessions, chat_titles):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []
        title = f"Новый чат {len(chat_titles) + 1}"
        chat_titles.append((title, chat_id))

    user_msg = {"role": "user", "content": format_message("user", message)}
    chat_sessions[chat_id].append(user_msg)

    value = None
    if len(chat_sessions[chat_id]) == 1:
        short_title = " ".join(message.strip().split()[:4]) + ("..." if len(message.strip().split()) > 4 else "")
        chat_titles = [(short_title if cid == chat_id else title, cid) for title, cid in chat_titles]
        value = short_title

    active_title = next((title for title, cid in chat_titles if cid == chat_id), None)
    choices = [t[0] for t in chat_titles]
    selected = value or active_title

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
    chat_titles = [(title, cid) for title, cid in chat_titles if cid != current_chat_id]
    
    # Выбираем новый текущий чат
    if chat_titles:
        new_current_id = chat_titles[-1][1]  # Берем последний чат
        new_choices = [t[0] for t in chat_titles]
        new_value = chat_titles[-1][0]
    else:
        # Если чатов не осталось, создаем новый
        new_current_id = str(uuid.uuid4())
        chat_sessions[new_current_id] = []
        title = "Новый чат 1"
        chat_titles.append((title, new_current_id))
        new_choices = [title]
        new_value = title
    
    print(f"Новый текущий чат: {new_current_id}")
    
    return new_current_id, chat_sessions, chat_titles, gr.update(
        choices=new_choices, 
        value=new_value
    )