import gradio as gr
from tools.db_tools.media_manager import replace_user_avatar, get_user_avatar_path
from tools.debug import logger
from ui.UI import UI


def on_avatar_change(file: str, user_id: int):
    """
    Вариант А: file — это СТРОКА с путем к временному файлу Gradio.
    Если file задан — читаем файл, заменяем аватар.
    Если file пустой — возвращаем текущий аватар (ничего не меняя).
    """
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

    

def on_avatar_change_btn(ui: UI):
    """
    Привязка единственной кнопки 'Изменить' к обработчику.
    Inputs: файл и user_id
    Outputs: preview, статус
    """
    ui.avatar_change_btn.click(
        fn=on_avatar_change,
        inputs=[ui.avatar_upload, ui.current_user_id],
        outputs=[ui.avatar_preview, ui.status_message]
    )
