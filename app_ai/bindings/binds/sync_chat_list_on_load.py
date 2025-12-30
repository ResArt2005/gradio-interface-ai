from ui.UI import UI
import gradio as gr
from components.chat_list import sync_chat_list

def sync_chat_list_on_load(ui: UI):
    """Привязка события синхронизации списка чатов при загрузке интерфейса."""
    def focus_textbox():
        return gr.update(autofocus=True)

    ui.interface.load(
        sync_chat_list,
        [ui.chat_titles, ui.current_chat_id],
        [ui.chat_list]
    ).then(focus_textbox, [], [ui.textbox])