from ui.UI import UI
import gradio as gr
from tools.fast_prompt_script import tree
from events.events import MAX_BUTTONS
from frontend.user_elements import (
    logout_user, open_settings_panel
)
def chat_list_column(ui: UI):
    # Левая колонка (список чатов)
    with gr.Column(scale=1):
        ui.new_chat_btn = gr.Button(value="+ Новый чат", elem_id="new_chat")
        ui.chat_list = gr.Radio(
            choices=[],
            label="Чаты",
            interactive=True,
            elem_id="chat_list",
            elem_classes="custom-radio"
        )
        open_settings_panel(ui)
        logout_user(ui)

def chatbot_column(ui: UI):
    # Правая колонка (чат)
    with gr.Column(scale=4):
        ui.chatbot = gr.Chatbot(
            label="Диалог",
            render_markdown=True,
            type="messages",
            elem_id="resizable-chat"
        )

        with gr.Row(elem_id="chips_row"):
            ui.chip_buttons = []
            for i in range(MAX_BUTTONS):
                label = tree[i]["name"] if i < len(tree) else ""
                visible = i < len(tree)
                ui.chip_buttons.append(
                    gr.Button(
                        value=label,
                        visible=visible,
                        elem_id=f"chip_{i}",
                        elem_classes="chip-button"
                    )
                )

        ui.textbox = gr.Textbox(
            placeholder="Введите вопрос.",
            lines=1,
            show_label=False,
            elem_id="main_input"
        )
        ui.clear = gr.Button("Очистить", elem_id="clear_chat")