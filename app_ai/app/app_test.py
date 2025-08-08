# app.py
import gradio as gr
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import uuid

# --- Настройки ---
FASTAPI_URL = "http://host.docker.internal:8000/query"

# --- Загрузка внешних файлов ---
try:
    with open("../styles.css", "r", encoding="utf-8") as f:
        CUSTOM_CSS = f.read()
except FileNotFoundError:
    CUSTOM_CSS = ""
    print("⚠️  Файл styles.css не найден")

try:
    with open("../script.js", "r", encoding="utf-8") as f:
        CUSTOM_JS = f.read()
except FileNotFoundError:
    CUSTOM_JS = ""
    print("⚠️  Файл script.js не найден")

# --- Вставка CSS и JS в <head> страницы ---
custom_head = f"""
<style>
{CUSTOM_CSS}
</style>
<script type="text/javascript">
// Выполняем после полной загрузки страницы
window.addEventListener('load', function () {{
    // Оборачиваем в IIFE, чтобы не засорять глобальное пространство
    (function () {{
        {CUSTOM_JS}
    }})();
}});
</script>
"""

# --- Форматирование сообщений с временем ---
def format_message(role, content):
    tz = os.getenv("TZ", "UTC")
    time_str = datetime.now(ZoneInfo(tz)).strftime("%H:%M:%S")
    name = "👤 **Пользователь**" if role == "user" else "🤖 **Ассистент**"
    return f"{name} [{time_str}]:\n\n{content}"

# --- Добавление сообщения от пользователя ---
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
    return "", chat_sessions[chat_id], chat_sessions, chat_titles, gr.update(
        choices=[t[0] for t in chat_titles],
        value=value or active_title
    )

# --- Получение ответа от LLM через FastAPI ---
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

# --- Создание нового чата ---
def new_chat(chat_sessions, chat_titles):
    new_id = str(uuid.uuid4())
    if any(cid == new_id for _, cid in chat_titles):
        return new_id, chat_sessions, chat_titles, gr.update(choices=[t[0] for t in chat_titles])
    chat_sessions[new_id] = []
    title = f"Новый чат {len(chat_titles) + 1}"
    chat_titles.append((title, new_id))
    return new_id, chat_sessions, chat_titles, gr.update(choices=[t[0] for t in chat_titles], value=title)

# --- Переключение между чатами ---
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
        ""  # очистить поле ввода
    )

# --- Gradio Интерфейс ---
with gr.Blocks(head=custom_head) as interface:
    gr.Markdown("## 💬 Чат с RAG")

    chat_sessions = gr.State({})
    current_chat_id = gr.State(str(uuid.uuid4()))
    chat_titles = gr.State([])

    with gr.Row():
        with gr.Column(scale=1):
            new_chat_btn = gr.Button("+ Новый чат")
            chat_list = gr.Radio(choices=[], label="Чаты", interactive=True)
            rename_box = gr.Textbox(placeholder="Переименовать чат", lines=1, show_label=False)
            rename_btn = gr.Button("Переименовать")
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                label="Диалог",
                render_markdown=True,
                type="messages",
                elem_id="resizable-chat"
            )
            textbox = gr.Textbox(placeholder="Введите вопрос...", lines=1, show_label=False)
            clear = gr.Button(value="Очистить", elem_id="clear_chat")

    # Логика отправки сообщения
    textbox.submit(
        add_user_message,
        [textbox, current_chat_id, chat_sessions, chat_titles],
        [textbox, chatbot, chat_sessions, chat_titles, chat_list]
    ).then(
        fetch_llm_answer,
        [textbox, current_chat_id, chat_sessions],
        [chatbot, chat_sessions]
    )

    # Очистка чата
    clear.click(
        lambda: ([], None),
        None,
        [chatbot, chat_sessions]
    )

    # Новый чат
    new_chat_btn.click(
        new_chat,
        [chat_sessions, chat_titles],
        [current_chat_id, chat_sessions, chat_titles, chat_list]
    )

    # Переключение чата
    chat_list.change(
        switch_chat,
        [chat_list, chat_titles, chat_sessions],
        [current_chat_id, chatbot]
    )

    # Переименование
    rename_btn.click(
        rename_chat,
        [rename_box, current_chat_id, chat_titles],
        [chat_titles, chat_list, rename_box]
    )

# --- Запуск приложения ---
if __name__ == "__main__":
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        # auth=("user", "password")  # при необходимости
    )