from __future__ import annotations
import gradio as gr
from typing import List, Dict, Optional


class UI:
    # ----- Главный элемент -----
    interface: Optional[gr.Blocks] = None
    # ----- Страницы -----
    # ----- Главная панель -----
    main_panel: Optional[gr.Column] = None
    # ----- Настройки -----
    settings_panel: Optional[gr.Column] = None
    # ----- Панель авторизации -----
    login_panel: Optional[gr.Column] = None
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

    # Авторизация
    login_panel: Optional[gr.Column] = None
    login_user: Optional[gr.Textbox] = None
    login_password: Optional[gr.Textbox] = None
    login_btn: Optional[gr.Button] = None
    login_status: Optional[gr.Text] = None
    btn_logout: Optional[gr.Button] = None
    # ----- Пользовательские данные -----
    authenticated: Optional[gr.State] = None
    current_user_id: Optional[gr.State] = None
    current_user_ip: Optional[gr.State] = None
    current_session_id: Optional[gr.State] = None
    e_mail: Optional[gr.State] = None
    last_name: Optional[gr.State] = None
    first_name: Optional[gr.State] = None
    surname: Optional[gr.State] = None
    current_password_txt: Optional[gr.State] = None
    new_password_txt: Optional[gr.State] = None
    confirm_new_password_txt: Optional[gr.State] = None
    password_change_btn: Optional[gr.Button] = None
    FIO_change_btn: Optional[gr.Button] = None
    email_change_btn: Optional[gr.Button] = None
    back_to_main_btn: Optional[gr.Button] = None
    open_settings_btn: Optional[gr.Button] = None
    # ----- Аватар -----
    avatar_preview: Optional[gr.Image] = None
    avatar_upload: Optional[gr.File] = None
    avatar_change_btn: Optional[gr.Button] = None
    status_message: Optional[gr.Text] = None