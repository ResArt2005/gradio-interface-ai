import gradio as gr
import uuid
from tools.debug import logger
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

    logger.success(f"Создан новый чат {chat_titles[new_id]} {new_id}")

    return new_id, chat_sessions, chat_titles, gr.update(
        choices=build_choices(chat_titles),
        value=new_id
    )

# --- Переключение чата ---
def switch_chat(chat_id, chat_titles, chat_sessions):
    if chat_id in chat_sessions:
        logger.info(f"Переключение на чат {chat_titles[chat_id]} {chat_id}")
        return chat_id, chat_sessions[chat_id]
    logger.error(f"Чат с ID {chat_id} не найден!")
    return gr.update(), []

# --- Переименование чата ---
def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip() or current_chat_id not in chat_titles:
        return gr.update(), gr.update(), ""
    logger.info(f"Чат {chat_titles[current_chat_id]} {current_chat_id} переименован в {new_title}")
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

    logger.info(f"Сообщение от пользователя: {message}")
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
    
    logger.success(f"Чат {chat_titles[current_chat_id]} {current_chat_id} успешно удалён.")

    chat_sessions.pop(current_chat_id, None)
    chat_titles.pop(current_chat_id, None) # Новый текущий чат: последний в словаре
    new_current_id = next(iter(chat_titles), None)
    
    logger.info(f"Переключение на чат {chat_titles[new_current_id]} {new_current_id}.")

    return new_current_id, chat_sessions, chat_titles, gr.update(
        choices=build_choices(chat_titles),
        value=new_current_id
        )