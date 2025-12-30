import gradio as gr
from tools.fast_prompt_script import tree

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
