from ui.UI import UI
import gradio as gr
from components.prompt_tree import reset_to_root
from components.chat_list import add_user_message 
from components.chat_utils import fetch_llm_answer 
def chat_message_flow(ui:UI):
    """Привязка событий для потока сообщений чата."""
    def focus_textbox():
        return gr.update(autofocus=True)

    ui.textbox.submit(
        add_user_message,
        inputs=[ui.textbox, ui.current_chat_id, ui.chat_sessions, ui.chat_titles, ui.current_user_id, ui.current_session_id],
        outputs=[ui.textbox, ui.chatbot, ui.chat_sessions, ui.chat_titles, ui.chat_list]
    ).then(
        fetch_llm_answer,
        [ui.textbox, ui.current_chat_id, ui.chat_sessions, ui.current_user_id, ui.current_session_id],
        [ui.chatbot, ui.chat_sessions]
    ).then(
        reset_to_root,
        [ui.top_tree_state],
        [*ui.chip_buttons, ui.current_nodes, ui.suppress_reset]
    ).then(
        focus_textbox, [], [ui.textbox]
    )