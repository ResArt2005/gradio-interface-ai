import gradio as gr
from tools.dbpg.DB_users import replace_user_avatar, get_user_avatar_path
from tools.debug import logger
def on_avatar_change(file: str, user_id: int):
    if not user_id:
        return None, "Ошибка: пользователь не авторизован"

    # --- Если файл загружен ---
    if file:
        try:
            # file — это строка: "/tmp/gradio/uploaded_image.png"
            with open(file, "rb") as f:
                file_bytes = f.read()

            ext = file.split(".")[-1].lower()

            new_path = replace_user_avatar(user_id, file_bytes, ext)

            logger.info("Аватар обновлён для user_id=%s -> %s", user_id, new_path)

            return f"/app/{new_path}", "Аватар обновлён!"

        except Exception as e:
            logger.error("Ошибка при сохранении аватара: %s", e)
            return None, f"Ошибка при сохранении: {e}"

    # --- Если файл НЕ выбран ---
    current = get_user_avatar_path(user_id)
    return (f"/app/{current}" if current else None), "Аватар не выбран"

def open_settings_panel():
    return gr.update(visible=False), gr.update(visible=True)

def back_to_main_panel():
    return gr.update(visible=True), gr.update(visible=False)