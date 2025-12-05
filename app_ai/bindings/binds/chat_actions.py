from ui.UI import UI
import gradio as gr
from components.chat_list import(
    new_chat, switch_chat, rename_chat, delete_chat
)
from components.chat_utils import clear_current_chat
def chat_actions(ui: UI):
    """Привязка событий для действий чата."""
    def focus_textbox():
        return gr.update(autofocus=True)
    #  CLEAR CHAT
    ui.clear.click(
        clear_current_chat,
        [ui.current_chat_id, ui.chat_sessions],
        [ui.chatbot, ui.chat_sessions]
    ).then(focus_textbox, [], [ui.textbox])
    #  NEW CHAT
    ui.new_chat_btn.click(
        new_chat,
        [ui.chat_sessions, ui.chat_titles, ui.current_user_id],
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