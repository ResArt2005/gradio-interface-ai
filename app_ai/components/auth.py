from tools.debug import logger
import gradio as gr
from tools.db_tools.DBPostgresqlGradio import db
def on_login_click(username, password):
            """
            Вызывается при клике 'Войти'. Возвращает:
              login_status,
              authenticated (State),
              current_user_id (State),
              login_panel visibility,
              main_panel visibility
            """
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
                return "Вход успешен", gr.update(True), user_id, gr.update(visible=False), gr.update(visible=True)
            except Exception as e:
                logger.error(f"Login error: {e}")
                return f"Ошибка при входе: {e}", gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False)

def on_logout_click(auth_state):
    """
    Выход: сбрасываем состояние аутентификации и показываем login_panel.
    """
    logger.info("User logged out (manual logout)")
    # Очистим сессию (при желании можно и другие state очистить)
    return gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False)