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

def email_settings_block(ui: UI):
    with gr.Row(elem_id="email_row", equal_height=True):
        ui.e_mail = gr.Textbox(
            label="E-mail",
            placeholder="Введите ваш e-mail",
            elem_id="email_textbox",
        )
        ui.email_change_btn = gr.Button(
            value="Изменить e-mail"
        )
    return ui.e_mail

def FIO_block(ui: UI):
    with gr.Row(elem_id="fio_row", equal_height=True):
        ui.last_name = gr.Textbox(
            label="Фамилия",
            placeholder="Введите вашу фамилию",
            elem_id="last_name_textbox",
        )
        ui.first_name = gr.Textbox(
            label="Имя",
            placeholder="Введите ваше имя",
            elem_id="first_name_textbox",
        )
        ui.surname = gr.Textbox(
            label="Отчество",
            placeholder="Введите ваше отчество",
            elem_id="surname_textbox",
        )
        ui.FIO_change_btn = gr.Button(
            value="Изменить ФИО",
            elem_id="FIO_change_btn"
        )
    return ui.last_name, ui.first_name, ui.surname

def change_password_block(ui: UI):
    with gr.Row(elem_id="change_password_row", equal_height=True):
        ui.current_password_txt = gr.Textbox(
            label="Текущий пароль",
            placeholder="Введите текущий пароль",
            elem_id="current_password_textbox",
            type="password",
        )
        ui.new_password_txt = gr.Textbox(
            label="Новый пароль",
            placeholder="Введите новый пароль",
            elem_id="new_password_textbox",
            type="password",
        )
        ui.confirm_new_password_txt = gr.Textbox(
            label="Подтвердите новый пароль",
            placeholder="Подтвердите новый пароль",
            elem_id="confirm_new_password_textbox",
            type="password",
        )
        ui.password_change_btn = gr.Button(
            value="Изменить пароль",
            elem_id="password_change_btn"
        )
    return ui.current_password_txt, ui.new_password_txt, ui.confirm_new_password_txt

def back_to_main_panel_button(ui: UI):
    with gr.Row():
        ui.back_to_main_btn = gr.Button(
            value="Назад",
            variant="secondary",
            elem_id="btn_back_to_main"
        )
    return ui.back_to_main_btn