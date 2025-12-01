import gradio as gr

from tools.db_tools.media_manager import (save_image,  save_image_path_to_db)
from tools.debug import logger
from ui.UI import UI

def on_avatar_save(file:dict, user_id:int):
    if file is None:
        return gr.update(), "Файл не выбран"
    logger.info("Текущий пользователь ID для аватара: %s", user_id)

    # читаем байты
    with open(file.name, "rb") as f:
        file_bytes = f.read()

    # определяем расширение
    ext = file.name.split(".")[-1].lower()

    # сохраняем в /app/media
    path = save_image(file_bytes, ext)

    # записываем путь в БД
    save_image_path_to_db(user_id, path)

    # превью должен показывать физический путь
    return f"/app/{path}", "Аватар обновлён!"

def on_avatar_save_btn(ui: UI):
    ui.avatar_save_btn.click(
    fn=on_avatar_save,
    inputs=[ui.avatar_upload, ui.current_user_id],
    outputs=[ui.avatar_preview, ui.status_message]
)