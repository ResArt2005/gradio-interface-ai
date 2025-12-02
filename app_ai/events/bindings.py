import gradio as gr
from ui.UI import UI
from tools.debug import logger
from events.events import (
    add_user_message, fetch_llm_answer, reset_to_root,
    clear_current_chat, new_chat, switch_chat, rename_chat,
    sync_chat_list, delete_chat,
    on_login_click, on_logout_click
)
from events.binds.chip_buttons import chip_buttons
from events.binds.textbox_change_events import textbox_change_events
from events.binds.on_avatar_change import on_avatar_change_btn
def bind_events(ui: UI):
    """Привязка всех событий Gradio к UI-компонентам."""
    #  CHIP BUTTONS
    def focus_textbox():
        return gr.update(autofocus=True)

    chip_buttons(ui)
    # TEXTBOX CHANGE EVENTS
    textbox_change_events(ui)
    #  CHAT MESSAGE FLOW
    ui.textbox.submit(
        add_user_message,
        inputs=[ui.textbox, ui.current_chat_id, ui.chat_sessions, ui.chat_titles],
        outputs=[ui.textbox, ui.chatbot, ui.chat_sessions, ui.chat_titles, ui.chat_list]
    ).then(
        fetch_llm_answer,
        [ui.textbox, ui.current_chat_id, ui.chat_sessions],
        [ui.chatbot, ui.chat_sessions]
    ).then(
        reset_to_root,
        [ui.top_tree_state],
        [*ui.chip_buttons, ui.current_nodes, ui.suppress_reset]
    ).then(
        focus_textbox, [], [ui.textbox]
    )
    #  CLEAR CHAT
    ui.clear.click(
        clear_current_chat,
        [ui.current_chat_id, ui.chat_sessions],
        [ui.chatbot, ui.chat_sessions]
    ).then(focus_textbox, [], [ui.textbox])
    #  NEW CHAT
    ui.new_chat_btn.click(
        new_chat,
        [ui.chat_sessions, ui.chat_titles],
        [ui.current_chat_id, ui.chat_sessions, ui.chat_titles, ui.chat_list]
    ).then(focus_textbox, [], [ui.textbox])
    #  SWITCH CHAT
    ui.chat_list.change(
        switch_chat,
        [ui.chat_list, ui.chat_titles, ui.chat_sessions],
        [ui.current_chat_id, ui.chatbot]
    ).then(focus_textbox, [], [ui.textbox])
    #  DELETE CHAT
    ui.delete_chat_btn.click(
        delete_chat,
        [ui.current_chat_id, ui.chat_sessions, ui.chat_titles],
        [ui.current_chat_id, ui.chat_sessions, ui.chat_titles, ui.chat_list]
    ).then(focus_textbox, [], [ui.textbox])
    #  RENAME CHAT
    ui.rename_btn_gr.click(
        rename_chat,
        [ui.rename_box, ui.current_chat_id, ui.chat_titles],
        [ui.chat_titles, ui.chat_list, ui.rename_box]
    ).then(focus_textbox, [], [ui.textbox])
    #  SYNC CHAT LIST ON LOAD
    ui.interface.load(
        sync_chat_list,
        [ui.chat_titles, ui.current_chat_id],
        [ui.chat_list]
    ).then(focus_textbox, [], [ui.textbox])
    #  LOGIN
    ui.login_btn.click(
        on_login_click,
        inputs=[ui.login_user, ui.login_password],
        outputs=[
            ui.login_status,
            ui.authenticated,
            ui.current_user_id,
            ui.login_panel,
            ui.main_panel,
            ui.avatar_preview
        ]
    )
    #  LOGOUT
    ui.btn_logout.click(
        on_logout_click,
        inputs=[ui.authenticated],
        outputs=[
            ui.authenticated,
            ui.current_user_id,
            ui.login_panel,
            ui.main_panel,
            ui.avatar_preview
        ]
    )
    on_avatar_change_btn(ui)
