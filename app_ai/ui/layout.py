import gradio as gr
import uuid
from pathlib import Path
from tools.fast_prompt_script import tree
from ui import events

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
        for i, btn in enumerate(chip_buttons):
            btn.click(
                events.chip_click,
                inputs=[gr.State(i), current_nodes, top_tree_state, suppress_reset, textbox],
                outputs=[textbox, *chip_buttons, current_nodes, suppress_reset]
            )

        textbox.change(
            events.on_textbox_change,
            inputs=[textbox, current_nodes, suppress_reset, top_tree_state],
            outputs=[*chip_buttons, current_nodes, suppress_reset]
        )

        def focus_textbox():
            return gr.update(autofocus=True)

        textbox.submit(
            events.add_user_message,
            [textbox, current_chat_id, chat_sessions, chat_titles],
            [textbox, chatbot, chat_sessions, chat_titles, chat_list]
        ).then(
            events.fetch_llm_answer,
            [textbox, current_chat_id, chat_sessions],
            [chatbot, chat_sessions]
        ).then(
            events.reset_to_root,
            [top_tree_state],
            [*chip_buttons, current_nodes, suppress_reset]
        ).then(
            focus_textbox, [], [textbox]
        )

        clear.click(
            events.clear_current_chat,
            [current_chat_id, chat_sessions],
            [chatbot, chat_sessions]
        ).then(focus_textbox, [], [textbox])

        new_chat_btn.click(
            events.new_chat,
            [chat_sessions, chat_titles],
            [current_chat_id, chat_sessions, chat_titles, chat_list]
        ).then(focus_textbox, [], [textbox])

        chat_list.change(
            events.switch_chat,
            [chat_list, chat_titles, chat_sessions],
            [current_chat_id, chatbot]
        ).then(focus_textbox, [], [textbox])

        rename_btn.click(
            events.rename_chat,
            [rename_box, current_chat_id, chat_titles],
            [chat_titles, chat_list, rename_box]
        ).then(focus_textbox, [], [textbox])

        interface.load(
            events.sync_chat_list,
            [chat_titles, current_chat_id],
            [chat_list]
        ).then(focus_textbox, [], [textbox])

    return interface
