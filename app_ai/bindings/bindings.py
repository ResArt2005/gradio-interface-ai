import gradio as gr
from ui.UI import UI
from bindings.binds.chip_buttons import chip_buttons
from bindings.binds.textbox_change_events import textbox_change_events
from bindings.binds.user_settings import open_settings_panel_btn, fio_change_btn, email_change_btn, password_change_btn, on_avatar_change_btn, on_avatar_upload_file, back_to_main_panel_btn
from bindings.binds.chat_message_flow import chat_message_flow
from bindings.binds.chat_actions import chat_actions
from bindings.binds.sync_chat_list_on_load import sync_chat_list_on_load
from bindings.binds.auth_btns import auth_btns

def bind_events(ui: UI):
    """Привязка всех событий Gradio к UI-компонентам."""
    chip_buttons(ui)
    # TEXTBOX CHANGE EVENTS
    textbox_change_events(ui)
    #  CHAT MESSAGE FLOW
    chat_message_flow(ui)
    # ACTIONS WITH CHAT
    chat_actions(ui)
    #  SYNC CHAT LIST ON LOAD
    sync_chat_list_on_load(ui)
    # AUTHORIZATION EVENTS
    auth_btns(ui)
    # OPEN SETTINGS PANEL EVENT
    open_settings_panel_btn(ui)
    # AVATAR CHANGE EVENT
    #on_avatar_upload_file(ui)
    on_avatar_change_btn(ui)
    # BACK TO MAIN PANEL EVENT
    back_to_main_panel_btn(ui)
    # FIO CHANGE EVENT
    fio_change_btn(ui)
    # EMAIL CHANGE EVENT
    email_change_btn(ui)
    # PASSWORD CHANGE EVENT
    password_change_btn(ui)