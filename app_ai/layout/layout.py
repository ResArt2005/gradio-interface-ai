import gradio as gr

from bindings.bindings import bind_events
from frontend.chat import chat_list_column, chatbot_column
from frontend.settings_element import (
    FIO_block,
    avatar_settings_block,
    back_to_main_panel_button,
    change_password_block,
    email_settings_block,
)
from frontend.unseen_elements import initialize_unseen_ui
from frontend.user_elements import authenticate_user, debug_panel
from static.load_static import *  # noqa: F403
from ui.UI import UI


# Основной layout
def build_interface()->gr.Blocks:
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
    """  # noqa: F405
    # Инициализация UI-контейнера
    ui = UI()
    with gr.Blocks(head=custom_head) as interface:
        ui.interface = interface
        gr.Markdown("## 💬 Чат с RAG")
        # Блок авторизации
        authenticate_user(ui)
        # Скрытые элементы для логики
        initialize_unseen_ui(ui)
        # Основная панель
        with gr.Column(visible=False, elem_id="main_panel") as ui.main_panel:
            with gr.Row():
                # Левая колонка (список чатов)
                chat_list_column(ui)
                # Правая колонка (чат)
                chatbot_column(ui)
        with gr.Column(visible=False, elem_id="settings_panel") as ui.settings_panel:
            debug_panel(ui)
            avatar_settings_block(ui)
            email_settings_block(ui)
            FIO_block(ui)
            change_password_block(ui)
            back_to_main_panel_button(ui)
        # Привязка событий
        bind_events(ui)

    return interface
