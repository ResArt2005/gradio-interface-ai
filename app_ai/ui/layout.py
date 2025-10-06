from typing import Dict
import gradio as gr
import uuid
from pathlib import Path
from tools.fast_prompt_script import tree
from events import events
from events.bindings import bind_events
BASE_DIR = Path(__file__).parent.parent

try:
    with open(BASE_DIR / "static/styles.css", "r", encoding="utf-8") as f:
        CUSTOM_CSS = f.read()
except FileNotFoundError:
    CUSTOM_CSS = ""

try:
    with open(BASE_DIR / "static/script.js", "r", encoding="utf-8") as f:
        CUSTOM_JS = f.read()
except FileNotFoundError:
    CUSTOM_JS = ""

custom_head = f"""
<style>
{CUSTOM_CSS}
</style>
<script type="text/javascript">
window.addEventListener('load', function () {{
    (function () {{
        {CUSTOM_JS}
    }})();
}});
</script>
"""

def build_interface():
    with gr.Blocks(head=custom_head) as interface:
        gr.Markdown("## 💬 Чат с RAG")

        chat_sessions = gr.State({})
        current_chat_id = gr.State(str(uuid.uuid4()))
        chat_titles: gr.State[Dict[str, str]] = gr.State({})

        top_tree_state = gr.State(tree)
        current_nodes = gr.State(tree)
        suppress_reset = gr.State(False)

        with gr.Row():
            with gr.Column(scale=1):
                new_chat_btn = gr.Button(value="+ Новый чат", elem_id="new_chat")
                chat_list = gr.Radio(
                    choices=[], 
                    label="Чаты", 
                    interactive=True, 
                    elem_id="chat_list", 
                    elem_classes="custom-radio"
                )
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    label="Диалог", render_markdown=True,
                    type="messages", elem_id="resizable-chat"
                )

                with gr.Row(elem_id="chips_row"):
                    chip_buttons = []
                    for i in range(events.MAX_BUTTONS):
                        if i < len(tree):
                            lbl = tree[i]["name"]
                            visible = True
                        else:
                            lbl = ""
                            visible = False
                        b = gr.Button(value=lbl, visible=visible, elem_id=f"chip_{i}", elem_classes="chip-button")
                        chip_buttons.append(b)

                textbox = gr.Textbox(
                    placeholder="Введите вопрос...", lines=1,
                    show_label=False, elem_id="main_input"
                )
                clear = gr.Button(value="Очистить", elem_id="clear_chat")

        #Невидимые элементы градио для кнтренней логики
        rename_btn_gr = gr.Button(value="gr_test", elem_id="gr_rename_chat")
        #Должен изменять current_chat_id
        burger_btn_gr = gr.Button(value="gr_test", elem_id="gr_burger")
        # Невидимое поле ввода, куда подставляется новое значение для переименования чата
        rename_box = gr.Textbox(placeholder="Переименовать чат", elem_id="gr_rename_box", lines=1, show_label=False)
        # Невидимая кнопка удаления чата
        delete_chat_btn = gr.Button(value="🗑️ Удалить чат", elem_id="gr_delete_chat", variant="stop")
        # --- Events binding ---
        bind_events((
            chip_buttons, textbox, chatbot, clear, new_chat_btn, chat_list,
            rename_btn_gr, rename_box, current_chat_id, chat_sessions,
            chat_titles, top_tree_state, current_nodes, suppress_reset, interface,
            delete_chat_btn
        ))

    return interface
