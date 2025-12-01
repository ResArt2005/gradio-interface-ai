import gradio as gr
from ui.UI import UI


def avatar_settings_block(ui:UI):
    # Элементы для работы с аватаром
    with gr.Row(elem_id="avatar_row", equal_height=True):
        # Превью (квадрат 40x40)
        ui.avatar_preview = gr.Image(
            label="",
            width=40,
            height=40,
            show_label=False,
            elem_id="avatar_preview",
            interactive=False,
            type="filepath",
        )

        # Загрузчик изображения
        ui.avatar_upload = gr.File(
            label="Загрузить аватар",
            file_types=["image"],
            elem_id="avatar_upload",
        )

        # Кнопка сохранить
        ui.avatar_save_btn = gr.Button(
            "Сохранить",
            elem_id="avatar_save_btn"
        )
        
        ui.status_message = gr.Text(label="Статус загрузки аватара", elem_id="avatar_status")
    return ui.avatar_preview, ui.avatar_upload, ui.avatar_save_btn
