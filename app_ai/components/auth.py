from tools.debug import logger
import gradio as gr
from tools.dbpg.DB_users import (
    get_user_avatar_path,
    get_user_fio,
    save_client_ip,
    verify_user_credentials,
    update_last_login,
    get_user_email
)
from tools.dbpg.DB_chats import download_chats_for_user
from components.chat_list import build_choices


def on_login_click(username, password, request: gr.Request):
    if not username or not password:
        return (
            "Введите логин и пароль",
            gr.update(),
            gr.update(),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(), gr.update(), gr.update(),
            gr.update(), gr.update(None),
            gr.update(None),
            gr.update(None)
        )

    try:
        user_id = verify_user_credentials(username, password)
        if user_id is None:
            logger.info(f"Failed login for {username}")
            return (
                "Неверный логин или пароль",
                gr.update(), gr.update(),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(None),
                gr.update(None),
                gr.update(None)
            )

        # Успешный вход
        ip = request.headers.get("x-forwarded-for", request.client.host)
        save_client_ip(user_id, ip)
        update_last_login(user_id)
        logger.success(f"User {username} (id={user_id}) logged in")

        # Пользовательские данные
        avatar_path = get_user_avatar_path(user_id)
        avatar_url = f"/app/{avatar_path}" if avatar_path else None
        first_name, last_name, surname = get_user_fio(user_id)
        e_mail = get_user_email(user_id)

        # Загружаем чаты
        chat_titles = download_chats_for_user(user_id)
        chat_sessions = {cid: [] for cid in chat_titles}  # ПУСТЫЕ истории

        choices = build_choices(chat_titles)

        logger.info(f"Loaded {len(chat_titles)} chats for user {username}")
        logger.debug(f"Chats: {chat_titles}")

        return (
            "Вход успешен",
            gr.update(True),
            user_id,
            gr.update(visible=False),
            gr.update(visible=True),
            avatar_url,
            first_name,
            last_name,
            surname,
            e_mail,

            chat_sessions,          # Состояние
            chat_titles,            # Состояние
            gr.update(choices=choices)
        )

    except Exception as e:
        logger.error(f"Login error: {e}")
        return (
            f"Ошибка при входе: {e}",
            gr.update(False),
            gr.update(None),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(None),
            gr.update(''), gr.update(''), gr.update(''),
            gr.update(''),
            gr.update(None), gr.update(None), gr.update(None)
        )

def on_logout_click(auth_state):
    logger.info("User logged out (manual logout)")
    return '', '', gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False), gr.update(None), gr.update(''), gr.update(''), gr.update(''), gr.update(''), gr.update(''), gr.update(None), gr.update(None), gr.update(None)