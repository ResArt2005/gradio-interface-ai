from ui.UI import UI
import gradio as gr
from tools.fast_prompt_script import tree
import uuid
def initialize_unseen_ui(ui: UI):
    
    # Инициализация состояний
    ui.chat_sessions = gr.State({})
    ui.current_chat_id = gr.State(str(uuid.uuid4()))
    ui.chat_titles = gr.State({})
    ui.top_tree_state = gr.State(tree)
    ui.current_nodes = gr.State(tree)
    ui.suppress_reset = gr.State(False)

    # Скрытые элементы для логики
    ui.rename_btn_gr = gr.Button(value="gr_test", elem_id="gr_rename_chat")
    ui.rename_box = gr.Textbox(placeholder="Переименовать чат", elem_id="gr_rename_box")
    ui.delete_chat_btn = gr.Button(value="🗑️ Удалить чат", variant="stop", elem_id="gr_delete_chat")