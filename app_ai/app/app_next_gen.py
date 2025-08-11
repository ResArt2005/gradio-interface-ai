import gradio as gr
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os, sys
import uuid
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.fast_prompt_script import tree

# --- Настройки ---
FASTAPI_URL = "http://host.docker.internal:8000/query"
BASE_DIR = Path(__file__).parent
# --- Загрузка внешних файлов ---
try:
    with open(BASE_DIR / "../static/styles.css", "r", encoding="utf-8") as f:
        CUSTOM_CSS = f.read()
except FileNotFoundError:
    CUSTOM_CSS = ""
    print("⚠️  Файл styles.css не найден")

try:
    with open(BASE_DIR / "../static/script.js", "r", encoding="utf-8") as f:
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

# -----------------------------
# --- Чипы (кнопки) над вводом ---
# -----------------------------
def max_buttons_in_tree(node_list):
    # возвращает максимальное число siblings на любом уровне
    if not node_list:
        return 0
    maxw = len(node_list)
    for n in node_list:
        children = n.get("children", [])
        if children:
            w = max_buttons_in_tree(children)
            if w > maxw:
                maxw = w
    return maxw

MAX_BUTTONS = max_buttons_in_tree(tree)

def format_buttons_for_level(nodes):
    """Возвращает список gr.update для всех MAX_BUTTONS кнопок."""
    updates = []
    for i in range(MAX_BUTTONS):
        if i < len(nodes):
            updates.append(gr.update(value=nodes[i]["name"], visible=True))
        else:
            updates.append(gr.update(visible=False))
    return updates

def chip_click(index, current_nodes_val, top_tree_val, suppress_reset_val, current_text):
    """
    При клике на чип:
      - добавляем текст к textbox
      - если есть children — показываем их
      - если детей нет — скрываем все кнопки
      - помечаем suppress_reset True (чтобы программная установка textbox не считалась ручной правкой)
    """
    no_ops = [gr.update() for _ in range(MAX_BUTTONS)]
    if not current_nodes_val or index >= len(current_nodes_val):
        return gr.update(), *no_ops, current_nodes_val, False

    node = current_nodes_val[index]
    node_name = node.get("name", "")
    children = node.get("children", [])

    # если есть дети — показываем их, если нет — список пуст (кнопки скрыты)
    new_level = children if children else []

    # добавляем текст
    new_text = (current_text.strip() + " " + node_name) if current_text.strip() else node_name

    btn_updates = format_buttons_for_level(new_level)
    return gr.update(value=new_text), *btn_updates, new_level, True

def on_textbox_change(text, current_nodes_val, suppress_reset_val, top_tree_val):
    """
    При изменении textbox:
      - если suppress_reset == True => это программная установка, сбрасываем флаг
      - иначе => пользователь вручную изменил текст => сбрасываем чипы на корень
      - если корень пустой — скрываем все кнопки
    """
    if suppress_reset_val:
        no_ops = [gr.update() for _ in range(MAX_BUTTONS)]
        return (*no_ops, current_nodes_val, False)
    else:
        btn_updates = format_buttons_for_level(top_tree_val if top_tree_val else [])
        return (*btn_updates, top_tree_val if top_tree_val else [], False)

def reset_to_root(top_tree_val):
    """Сброс чипов на корень (используется после submit)."""
    btn_updates = format_buttons_for_level(top_tree_val)
    return (*btn_updates, top_tree_val, False)

# -----------------------------
# --- Gradio Интерфейс ---
# -----------------------------
with gr.Blocks(head=custom_head) as interface:
    gr.Markdown("## 💬 Чат с RAG")

    chat_sessions = gr.State({})
    current_chat_id = gr.State(str(uuid.uuid4()))
    chat_titles = gr.State([])

    # состояния для чипов
    top_tree_state = gr.State(tree)
    current_nodes = gr.State(tree)      # текущий набор узлов, соответствующий видимым чипам
    suppress_reset = gr.State(False)    # флаг: было ли программное изменение textbox

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

            # --- Чипы (кнопки) над полем ввода ---
            with gr.Row(elem_id="chips_row"):
                chip_buttons = []
                for i in range(MAX_BUTTONS):
                    if i < len(tree):
                        lbl = tree[i]["name"]
                        visible = True
                    else:
                        lbl = ""
                        visible = False
                    b = gr.Button(value=lbl, visible=visible, elem_id=f"chip_{i}")
                    chip_buttons.append(b)

            textbox = gr.Textbox(placeholder="Введите вопрос...", lines=1, show_label=False)
            clear = gr.Button(value="Очистить", elem_id="clear_chat")

    # Привязки событий
    # Каждый чип вызывает chip_click с соответствующим index
    btn:gr.Button
    for i, btn in enumerate(chip_buttons):
        btn.click(
            chip_click,
            inputs=[gr.State(i), current_nodes, top_tree_state, suppress_reset, textbox],
            outputs=[textbox, *chip_buttons, current_nodes, suppress_reset]
        )

    # Изменение textbox
    textbox.change(
        on_textbox_change,
        inputs=[textbox, current_nodes, suppress_reset, top_tree_state],
        outputs=[*chip_buttons, current_nodes, suppress_reset]
    )

    # Логика отправки сообщения: add_user_message -> fetch_llm_answer -> reset_to_root
    textbox.submit(
        add_user_message,
        [textbox, current_chat_id, chat_sessions, chat_titles],
        [textbox, chatbot, chat_sessions, chat_titles, chat_list]
    ).then(
        fetch_llm_answer,
        [textbox, current_chat_id, chat_sessions],
        [chatbot, chat_sessions]
    ).then(
        reset_to_root,
        [top_tree_state],
        [*chip_buttons, current_nodes, suppress_reset]
    )

    # Очистка чата (оставил поведение как было)
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
