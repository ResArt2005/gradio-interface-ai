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
        chat_titles = gr.State([])

        top_tree_state = gr.State(tree)
        current_nodes = gr.State(tree)
        suppress_reset = gr.State(False)

        with gr.Row():
            with gr.Column(scale=1):
                new_chat_btn = gr.Button("+ Новый чат")
                chat_list = gr.Radio(choices=[], label="Чаты", interactive=True)
                rename_box = gr.Textbox(placeholder="Переименовать чат", lines=1, show_label=False)
                rename_btn = gr.Button("Переименовать")
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
                        b = gr.Button(value=lbl, visible=visible, elem_id=f"chip_{i}")
                        chip_buttons.append(b)

                textbox = gr.Textbox(
                    placeholder="Введите вопрос...", lines=1,
                    show_label=False, elem_id="main_input"
                )
                clear = gr.Button(value="Очистить", elem_id="clear_chat")

        # --- Events binding ---
        bind_events((
            chip_buttons, textbox, chatbot, clear, new_chat_btn, chat_list,
            rename_btn, rename_box, current_chat_id, chat_sessions,
            chat_titles, top_tree_state, current_nodes, suppress_reset, interface
        ))

    return interface
