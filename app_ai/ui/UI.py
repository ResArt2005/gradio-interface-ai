from __future__ import annotations
import gradio as gr
from typing import List, Dict, Optional


class UI:
    """
    Контейнер всех UI-компонентов Gradio.
    Упрощает передачу элементов в бинды и улучшает читаемость.
    """

    # ----- Основные элементы -----
    interface: Optional[gr.Blocks] = None

    # Авторизация
    login_panel: Optional[gr.Column] = None
    main_panel: Optional[gr.Column] = None
    login_user: Optional[gr.Textbox] = None
    login_password: Optional[gr.Textbox] = None
    login_btn: Optional[gr.Button] = None
    login_status: Optional[gr.Text] = None
    btn_logout: Optional[gr.Button] = None

    authenticated: Optional[gr.State] = None
    current_user_id: Optional[gr.State] = None

    # ----- Чат -----
    chat_list: Optional[gr.Radio] = None
    new_chat_btn: Optional[gr.Button] = None
    delete_chat_btn: Optional[gr.Button] = None
    rename_btn_gr: Optional[gr.Button] = None
    rename_box: Optional[gr.Textbox] = None
    chatbot: Optional[gr.Chatbot] = None

    textbox: Optional[gr.Textbox] = None
    clear: Optional[gr.Button] = None

    chip_buttons: List[gr.Button] = []
    current_chat_id: Optional[gr.State] = None
    chat_sessions: Optional[gr.State] = None
    chat_titles: Optional[gr.State] = None

    # ----- Тематические состояния -----
    top_tree_state: Optional[gr.State] = None
    current_nodes: Optional[gr.State] = None
    suppress_reset: Optional[gr.State] = None

    # ----- Аватар -----
    avatar_preview: Optional[gr.Image] = None
    avatar_upload: Optional[gr.File] = None
    avatar_change_btn: Optional[gr.Button] = None
    status_message: Optional[gr.Text] = None
    # ----- Прочее -----