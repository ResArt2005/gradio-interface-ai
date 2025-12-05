import gradio as gr
import uuid
from tools.debug import logger
from tools.dbpg.DB_chats import save_new_chat, delete_chat_from_bd, rename_chat_in_bd
from tools.dbpg.DB_messages import save_message 
# --- Синхронизация списка чатов ---
def sync_chat_list(chat_titles, current_chat_id):
    if not chat_titles:
        return gr.update(choices=[])
    return gr.update(choices=build_choices(chat_titles), value=current_chat_id)

# --- Добавление сообщения ---
def add_user_message(message, chat_id, chat_sessions, chat_titles, user_id=None, session_id=None):
    """
    Добавить сообщение от пользователя в chat_sessions и в БД.
    Новая сигнатура принимает user_id и session_id (optional).
    Возвращает tuple, совместимый с тем, что ожидает bindings/layout.
    """
    # Если чатов нет, создаём новый (локально) — как и раньше
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []
        chat_title = message[:30] + "..." if len(message) > 30 else message
        chat_titles[chat_id] = chat_title

    # Добавляем сообщение пользователя в память
    user_msg = {"role": "user", "content": message}
    chat_sessions[chat_id].append(user_msg)

    # Сохраняем в БД: если user_id не передан, сохраняем с NULL user_id
    try:
        save_message(chat_id=chat_id, user_id=user_id, role='user', content=message, session_id=session_id)
    except Exception as e:
        # Не фатальная ошибка: логируем и продолжаем
        from tools.debug import logger
        logger.error(f"Failed to save user message to DB: {e}")

    return (
        gr.update(value="", autofocus=True),
        chat_sessions[chat_id],  # content for chatbot
        chat_sessions,           # updated state
        chat_titles,             # updated state
        gr.update(choices=build_choices(chat_titles), value=chat_id)
    )

def build_choices(chat_titles: dict):
    return [(title, cid) for cid, title in chat_titles.items()]


# --- Новый чат ---
def new_chat(chat_sessions, chat_titles, user_id, session_id=None):
    # unchanged logic but pass session_id if you want to create initial message later
    new_id = str(uuid.uuid4())
    chat_sessions[new_id] = []

    base = "Новый чат"
    i = 1
    existing = set(chat_titles.values())
    while f"{base} {i}" in existing:
        i += 1
    chat_titles[new_id] = f"{base} {i}"

    # Save chat in DB (unchanged)
    from tools.dbpg.DB_chats import save_new_chat
    save_new_chat(new_id, chat_titles[new_id], user_id, session_id)
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
