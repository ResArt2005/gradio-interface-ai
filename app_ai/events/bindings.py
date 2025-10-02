import gradio as gr
from events.events import (
    chip_click, on_textbox_change, add_user_message, fetch_llm_answer,
    reset_to_root, clear_current_chat, new_chat, switch_chat, rename_chat, sync_chat_list
)

def bind_events(components:tuple):
    (
        chip_buttons, textbox, chatbot, clear, new_chat_btn, chat_list,
        rename_btn, rename_box, current_chat_id, chat_sessions,
        chat_titles, top_tree_state, current_nodes, suppress_reset, interface,
        burger_btn_gr
    ) = components

    # --- Events binding ---
    for i, btn in enumerate(chip_buttons):
        btn.click(
            chip_click,
            inputs=[gr.State(i), current_nodes, top_tree_state, suppress_reset, textbox],
            outputs=[textbox, *chip_buttons, current_nodes, suppress_reset]
        )

    textbox.change(
        on_textbox_change,
        inputs=[textbox, current_nodes, suppress_reset, top_tree_state],
        outputs=[*chip_buttons, current_nodes, suppress_reset]
    )

    def focus_textbox():
        return gr.update(autofocus=True)

    textbox.submit(
        add_user_message,
        [textbox, current_chat_id, chat_sessions, chat_titles],
        [textbox, chatbot, chat_sessions, chat_titles, chat_list]
    ).then(fetch_llm_answer, [textbox, current_chat_id, chat_sessions], [chatbot, chat_sessions]
    ).then(reset_to_root, [top_tree_state], [*chip_buttons, current_nodes, suppress_reset]
    ).then(focus_textbox, [], [textbox])

    clear.click(clear_current_chat, [current_chat_id, chat_sessions], [chatbot, chat_sessions]
    ).then(focus_textbox, [], [textbox])

    new_chat_btn.click(new_chat, [chat_sessions, chat_titles],
                       [current_chat_id, chat_sessions, chat_titles, chat_list]
    ).then(focus_textbox, [], [textbox])

    chat_list.change(switch_chat, [chat_list, chat_titles, chat_sessions],
                     [current_chat_id, chatbot]
    ).then(focus_textbox, [], [textbox])
    
    # На тестировании
    burger_btn_gr.click(rename_chat, [chat_list, chat_titles],
                     [current_chat_id]
    ).then(focus_textbox, [], [textbox])

    rename_btn.click(rename_chat, [rename_box, current_chat_id, chat_titles],
                     [chat_titles, chat_list, rename_box]
    ).then(focus_textbox, [], [textbox])

    interface.load(sync_chat_list, [chat_titles, current_chat_id], [chat_list]
    ).then(focus_textbox, [], [textbox])