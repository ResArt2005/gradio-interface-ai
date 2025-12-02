import gradio as gr
from ui.UI import UI


def avatar_settings_block(ui: UI):
    with gr.Row(elem_id="avatar_row", equal_height=True):
        ui.avatar_preview = gr.Image(
            label="",
            width=40,
            height=40,
            show_label=False,
            elem_id="avatar_preview",
            interactive=False,
            type="filepath",
        )

        ui.avatar_upload = gr.File(
            label="Выбрать файл",
            file_types=["image"],
            elem_id="avatar_upload",
        )

        ui.avatar_change_btn = gr.Button(
            value="Изменить",
            elem_id="avatar_change_btn"
        )

    ui.status_message = gr.Markdown("", elem_id="avatar_status")

    return ui.avatar_preview, ui.avatar_upload, ui.avatar_change_btn
