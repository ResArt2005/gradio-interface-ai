from tools.debug import logger
import gradio as gr
from tools.dbpg.DBPostgresqlGradio import db
from tools.dbpg.DB_users import get_user_avatar_path, get_user_fio, save_client_ip, verify_user_credentials, update_last_login, get_user_email
from tools.dbpg.DB_chats import download_chats_for_user
def on_login_click(username, password, request: gr.Request):
    if not username or not password:
        return "Введите логин и пароль", gr.update(), gr.update(), gr.update(visible=True), gr.update(visible=False), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(None), gr.update(None), gr.update(None)
    try:
        user_id = verify_user_credentials(username, password)
        if user_id is None:
            logger.info(f"Failed login for {username}")
            return "Неверный логин или пароль", gr.update(), gr.update(), gr.update(visible=True), gr.update(visible=False), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(None), gr.update(None), gr.update(None)
        # Успешный вход
        ip = request.headers.get("x-forwarded-for", request.client.host)
        save_client_ip(user_id, ip)
        update_last_login(user_id)
        logger.success(f"User {username} (id={user_id}) logged in")
        # Скрываем login_panel и показываем main_panel; устанавливаем auth state
        avatar_path = get_user_avatar_path(user_id)
        avatar_url = f"/app/{avatar_path}" if avatar_path else None
        first_name, last_name, surname = get_user_fio(user_id)
        e_mail = get_user_email(user_id)
        # Выгрузка чатов
        chat_titles = download_chats_for_user(user_id)
        chat_sessions = {cid: [] for cid in chat_titles}     # пустые истории
        choices = list(chat_titles.values())
        logger.info(f"Loaded {len(chat_titles)} chats for user {username} (id={user_id})")
        logger.debug(f"Chats: {chat_titles}")
        return (
            "Вход успешен",
            gr.update(True),              # authenticated
            user_id,                      # user_id
            gr.update(visible=False),     # login_panel
            gr.update(visible=True),      # main_panel
            avatar_url,
            first_name,
            last_name,
            surname,
            e_mail,

            gr.update(chat_sessions),     # State dict
            gr.update(chat_titles),       # State dict
            gr.update(choices=choices)    # list[str]
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        return f"Ошибка при входе: {e}", gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False), gr.update(None), gr.update(''), gr.update(''), gr.update(''), gr.update(''), gr.update(''), gr.update(None), gr.update(None), gr.update(None)

def on_logout_click(auth_state):
    logger.info("User logged out (manual logout)")
    return '', '', gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False), gr.update(None), gr.update(''), gr.update(''), gr.update(''), gr.update(''), gr.update(''), gr.update(None), gr.update(None), gr.update(None)