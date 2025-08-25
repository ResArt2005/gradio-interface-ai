import gradio as gr
from tools.chat_utils import (
    clear_current_chat, fetch_llm_answer, new_chat, switch_chat, rename_chat, format_message
)
from tools.fast_prompt_script import tree

# --- Синхронизация чатов ---
def sync_chat_list(chat_titles, current_chat_id):
    titles = [t for t, _ in chat_titles]
    active = next((t for t, cid in chat_titles if cid == current_chat_id), None)
    if not titles:
        return gr.update(choices=[])
    return gr.update(choices=titles, value=active)

# --- Добавление сообщения ---
def add_user_message(message, chat_id, chat_sessions, chat_titles):
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []
        title = f"Новый чат {len(chat_titles) + 1}"
        chat_titles.append((title, chat_id))

    user_msg = {"role": "user", "content": format_message("user", message)}
    chat_sessions[chat_id].append(user_msg)

    value = None
    if len(chat_sessions[chat_id]) == 1:
        short_title = " ".join(message.strip().split()[:4]) + ("..." if len(message.strip().split()) > 4 else "")
        chat_titles = [(short_title if cid == chat_id else title, cid) for title, cid in chat_titles]
        value = short_title

    active_title = next((title for title, cid in chat_titles if cid == chat_id), None)
    choices = [t[0] for t in chat_titles]
    selected = value or active_title

    if selected not in choices:
        return gr.update(value="", autofocus=True), chat_sessions[chat_id], chat_sessions, chat_titles, gr.update(choices=choices)

    return gr.update(value="", autofocus=True), chat_sessions[chat_id], chat_sessions, chat_titles, gr.update(
        choices=choices, value=selected
    )

# --- Чипы (Prompt Tree) ---
def max_buttons_in_tree(node_list):
    if not node_list:
        return 0
    maxw = len(node_list)
    for n in node_list:
        children = n.get("children", [])
        if children:
            w = max_buttons_in_tree(children)
            if w > maxw:
                maxw = w
    return maxw

MAX_BUTTONS = max_buttons_in_tree(tree)

def format_buttons_for_level(nodes):
    updates = []
    for i in range(MAX_BUTTONS):
        if i < len(nodes):
            updates.append(gr.update(value=nodes[i]["name"], visible=True))
        else:
            updates.append(gr.update(visible=False))
    return updates

def chip_click(index, current_nodes_val, top_tree_val, suppress_reset_val, current_text):
    no_ops = [gr.update() for _ in range(MAX_BUTTONS)]
    if not current_nodes_val or index >= len(current_nodes_val):
        return gr.update(), *no_ops, current_nodes_val, False

    node = current_nodes_val[index]
    node_name = node.get("name", "")
    children = node.get("children", [])

    new_level = children if children else []
    new_text = (current_text.strip() + " " + node_name) if current_text.strip() else node_name
    btn_updates = format_buttons_for_level(new_level)
    return gr.update(value=new_text, autofocus=True), *btn_updates, new_level, True

def on_textbox_change(text, current_nodes_val, suppress_reset_val, top_tree_val):
    if suppress_reset_val:
        no_ops = [gr.update() for _ in range(MAX_BUTTONS)]
        return (*no_ops, current_nodes_val, False)
    else:
        btn_updates = format_buttons_for_level(top_tree_val if top_tree_val else [])
        return (*btn_updates, top_tree_val if top_tree_val else [], False)

def reset_to_root(top_tree_val):
    btn_updates = format_buttons_for_level(top_tree_val)
    return (*btn_updates, top_tree_val, False)
