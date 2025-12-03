import gradio as gr
from ui.UI import UI
from events.binds.chip_buttons import chip_buttons
from events.binds.textbox_change_events import textbox_change_events
from events.binds.user_settings import open_settings_panel_btn, on_avatar_change_btn, back_to_main_panel_btn
from events.binds.chat_message_flow import chat_message_flow
from events.binds.chat_actions import chat_actions
from events.binds.sync_chat_list_on_load import sync_chat_list_on_load
from events.binds.auth_btns import auth_btns

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
    on_avatar_change_btn(ui)
    # BACK TO MAIN PANEL EVENT
    back_to_main_panel_btn(ui)
