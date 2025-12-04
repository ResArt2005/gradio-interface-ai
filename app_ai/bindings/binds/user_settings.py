from components.user_manager import on_avatar_change, fio_change, open_settings_panel, back_to_main_panel, email_change
from ui.UI import UI
    

def on_avatar_change_btn(ui: UI):
    ui.avatar_change_btn.click(
        fn=on_avatar_change,
        inputs=[ui.avatar_upload, ui.current_user_id],
        outputs=[ui.avatar_preview, ui.status_message]
    )

def open_settings_panel_btn(ui: UI):
    ui.open_settings_btn.click(
        fn=open_settings_panel,
        inputs=[],
        outputs=[ui.main_panel, ui.settings_panel]
    )

def back_to_main_panel_btn(ui: UI):
    ui.back_to_main_btn.click(
        fn=back_to_main_panel,
        inputs=[],
        outputs=[ui.main_panel, ui.settings_panel, ui.status_message]
    )

def fio_change_btn(ui: UI):
    ui.FIO_change_btn.click(
        fio_change,
        inputs=[ui.first_name, ui.last_name, ui.surname, ui.current_user_id],
        outputs=[ui.first_name, ui.last_name, ui.surname, ui.status_message]
    )

def email_change_btn(ui: UI):
    ui.email_change_btn.click(
        email_change,
        inputs=[ui.e_mail, ui.current_user_id],
        outputs=[ui.e_mail, ui.status_message]
    )