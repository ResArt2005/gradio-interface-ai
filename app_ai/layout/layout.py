# ui/layout.py
from typing import Dict
import uuid
import gradio as gr

from tools.fast_prompt_script import tree
from events.events import MAX_BUTTONS
from events.bindings import bind_events
from static.load_static import *
from tools.debug import logger
from ui.UI import UI
from frontend.authenticate_user import (
    authenticate_user
)
# Основной layout
def build_interface():
    ui = UI()
    custom_head = f"""
    <style>{styles_css}</style>
    <script>
    window.addEventListener('load', function () {{
        (function () {{
            {customResizable_js}
            {simulateClickById_js}
            {fucusInput_js}
            {Btn_Rename_js}
            {Btn_Delete_js}
            {burgerMenu_js}
            {script_js}
        }})();
    }});
    </script>
    """
    with gr.Blocks(head=custom_head) as interface:
        ui.interface = interface
        gr.Markdown("## 💬 Чат с RAG")
        # Блок авторизации
        authenticate_user(ui)
        # Основная панель (пока скрыта)
        with gr.Column(visible=False, elem_id="main_panel") as ui.main_panel:

            with gr.Row():
                ui.btn_logout = gr.Button(value="Выйти", variant="secondary", elem_id="btn_logout")
                gr.Markdown("")

            ui.chat_sessions = gr.State({})
            ui.current_chat_id = gr.State(str(uuid.uuid4()))
            ui.chat_titles = gr.State({})

            ui.top_tree_state = gr.State(tree)
            ui.current_nodes = gr.State(tree)
            ui.suppress_reset = gr.State(False)

            with gr.Row():
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
            # Скрытые элементы для логики
            ui.rename_btn_gr = gr.Button(value="gr_test", elem_id="gr_rename_chat")
            ui.rename_box = gr.Textbox(placeholder="Переименовать чат", elem_id="gr_rename_box")
            ui.delete_chat_btn = gr.Button(value="🗑️ Удалить чат", variant="stop", elem_id="gr_delete_chat")
        # Привязка событий
        bind_events(ui)

    return interface
