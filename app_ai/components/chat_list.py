import gradio as gr
import uuid
from tools.debug import logger
from tools.dbpg.DB_chats import save_new_chat, delete_chat_from_bd, rename_chat_in_bd

# --- Синхронизация списка чатов ---
def sync_chat_list(chat_titles, current_chat_id):
    if not chat_titles:
        return gr.update(choices=[])
    return gr.update(choices=build_choices(chat_titles), value=current_chat_id)

# --- Добавление сообщения ---
def add_user_message(message, chat_id, chat_sessions, chat_titles):
    # Если чатов нет, создаем новый чат с тем же chat_id
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []
        chat_title = message[:30] + "..." if len(message) > 30 else message
        chat_titles[chat_id] = chat_title
        logger.info(f"Создан новый чат: {chat_title} {chat_id}")
    
    # Добавляем сообщение пользователя
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

def build_choices(chat_titles: dict):
    return [(title, cid) for cid, title in chat_titles.items()]


# --- Новый чат ---
def new_chat(chat_sessions, chat_titles, user_id):
    new_id = str(uuid.uuid4())
    chat_sessions[new_id] = []

    base = "Новый чат"
    i = 1
    existing = set(chat_titles.values())
    while f"{base} {i}" in existing:
        i += 1
    chat_titles[new_id] = f"{base} {i}"

    save_new_chat(new_id, chat_titles[new_id], user_id)
    logger.success(f"Создан новый чат {chat_titles[new_id]} {new_id}")

    return (
        new_id,
        chat_sessions,
        chat_titles,
        gr.update(choices=build_choices(chat_titles), value=new_id)
    )


# --- Переключение чата ---
def switch_chat(chat_id, chat_titles, chat_sessions):
    if chat_id in chat_sessions:
        logger.info(f"Переключение в чат {chat_titles[chat_id]} {chat_id}")
        return (
            chat_id,
            chat_sessions[chat_id],
            chat_sessions,
            chat_titles
        )

    logger.warning(f"Чат {chat_id} не найден!")
    return (
        gr.update(),     # current_chat_id
        [],              # chatbot
        chat_sessions,   # ВАЖНО: НЕ СБРАСЫВАЕМ
        chat_titles
    )


# --- Переименование чата ---
def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip() or current_chat_id not in chat_titles:
        return chat_titles, gr.update(), ""

    logger.info(f"Переименование чата {current_chat_id} → {new_title}")

    chat_titles[current_chat_id] = new_title
    rename_chat_in_bd(current_chat_id, new_title)

    return (
        chat_titles,
        gr.update(choices=build_choices(chat_titles), value=current_chat_id),
        ""
    )


# --- Удаление чата ---
def delete_chat(current_chat_id, chat_sessions, chat_titles):
    if not current_chat_id:
        return (
            gr.update(),
            chat_sessions,
            chat_titles,
            gr.update()
        )

    logger.success(f"Удаление чата {chat_titles[current_chat_id]} ({current_chat_id})")

    delete_chat_from_bd(current_chat_id)
    chat_sessions.pop(current_chat_id, None)
    chat_titles.pop(current_chat_id, None)

    new_id = next(iter(chat_titles), None) if chat_titles else None

    return (
        new_id,
        chat_sessions,
        chat_titles,
        gr.update(choices=build_choices(chat_titles), value=new_id)
    )
