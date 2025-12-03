from tools.debug import logger
import gradio as gr
from tools.dbpg.DBPostgresqlGradio import db
from components.avatar_manager import get_user_avatar_path
def on_login_click(username, password):
            if not username or not password:
                return "Введите логин и пароль", gr.update(), gr.update(), gr.update(visible=True), gr.update(visible=False)
            try:
                user_id = db.verify_user_credentials(username, password)
                if user_id is None:
                    logger.info(f"Failed login for {username}")
                    return "Неверный логин или пароль", gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False)
                # Успешный вход
                db.update_last_login(user_id)
                logger.success(f"User {username} (id={user_id}) logged in")
                # Скрываем login_panel и показываем main_panel; устанавливаем auth state
                avatar_path = get_user_avatar_path(user_id)
                avatar_url = f"/app/{avatar_path}" if avatar_path else None
                return "Вход успешен", gr.update(True), user_id, gr.update(visible=False), gr.update(visible=True), avatar_url
            except Exception as e:
                logger.error(f"Login error: {e}")
                return f"Ошибка при входе: {e}", gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False)

def on_logout_click(auth_state):
    logger.info("User logged out (manual logout)")
    return gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False), gr.update(None), gr.update(None)