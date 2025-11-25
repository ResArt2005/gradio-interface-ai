from typing import Dict
import gradio as gr
import uuid
from tools.fast_prompt_script import tree
from events.events import MAX_BUTTONS
from events.bindings import bind_events
from static.load_static import *
from tools.DBPostgresqlGradio import db  # Используем инстанс db из tools (см. DBPostgresqlGradio.py)
from tools.debug import logger

custom_head = f"""
<style>
{styles_css}
</style>
<script type="text/javascript">
window.addEventListener('load', function () {{
    (function () {{
        //Блоки по умолчанию
        {customResizable_js}
        {simulateClickById_js}
        {fucusInput_js}
        //Напрямую влияющие на разметку
        // == Бургер меню и его компоненты ==
        {Btn_Rename_js}
        {Btn_Delete_js}
        {burgerMenu_js}
        // == Другое ==
        //Связующий блок, который заставляет работать остальные js скрипты
        {script_js}
    }})();
}});
</script>
"""

def build_interface():
    with gr.Blocks(head=custom_head) as interface:
        gr.Markdown("## 💬 Чат с RAG")

        # --- Authentication state ---
        authenticated = gr.State(False)
        current_user_id = gr.State(None)

        # --- Login panel (visible by default) ---
        with gr.Column(visible=True, elem_id="login_panel") as login_panel:
            gr.Markdown("### Вход")
            login_user = gr.Textbox(label="Логин", placeholder="Введите логин", lines=1)
            login_password = gr.Textbox(label="Пароль", placeholder="Введите пароль", lines=1, type="password")
            login_btn = gr.Button(value="Войти")
            login_status = gr.Text(value="", interactive=False)

        # --- Main app panel (hidden until authenticated) ---
        with gr.Column(visible=False, elem_id="main_panel") as main_panel:
            # верхняя строка с кнопкой выхода
            with gr.Row():
                btn_logout = gr.Button(value="Выйти", variant="secondary", elem_id="btn_logout")
                gr.Markdown("")  # spacer

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
                        for i in range(MAX_BUTTONS):
                            if i < len(tree):
                                lbl = tree[i]["name"]
                                visible = True
                            else:
                                lbl = ""
                                visible = False
                            b = gr.Button(value=lbl, visible=visible, elem_id=f"chip_{i}", elem_classes="chip-button")
                            chip_buttons.append(b)

                    textbox = gr.Textbox(
                        placeholder="Введите вопрос.", lines=1,
                        show_label=False, elem_id="main_input"
                    )
                    clear = gr.Button(value="Очистить", elem_id="clear_chat")

            # Невидимые элементы градио для внутренней логики
            rename_btn_gr = gr.Button(value="gr_test", elem_id="gr_rename_chat")
            rename_box = gr.Textbox(placeholder="Переименовать чат", elem_id="gr_rename_box", lines=1, show_label=False)
            delete_chat_btn = gr.Button(value="🗑️ Удалить чат", elem_id="gr_delete_chat", variant="stop")
            # --- Events binding ---
            bind_events((
                chip_buttons, textbox, chatbot, clear, new_chat_btn, chat_list,
                rename_btn_gr, rename_box, current_chat_id, chat_sessions,
                chat_titles, top_tree_state, current_nodes, suppress_reset, interface,
                delete_chat_btn
            ))

        # -----------------------
        # Callbacks: login, logout
        # -----------------------
        def on_login_click(username, password):
            """
            Вызывается при клике 'Войти'. Возвращает:
              login_status,
              authenticated (State),
              current_user_id (State),
              login_panel visibility,
              main_panel visibility
            """
            if not username or not password:
                return "Введите логин и пароль", gr.update(), gr.update(), gr.update(visible=True), gr.update(visible=False)
            try:
                user_id = db.verify_user_credentials(username, password)
                if user_id is None:
                    logger.info(f"Failed login for {username}")
                    return "Неверный логин или пароль", gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False)
                # Успешный вход
                db.update_last_login(user_id)
                logger.success(f"User {username} (id={user_id}) logged in")
                # Скрываем login_panel и показываем main_panel; устанавливаем auth state
                return "Вход успешен", gr.update(True), gr.update(user_id), gr.update(visible=False), gr.update(visible=True)
            except Exception as e:
                logger.error(f"Login error: {e}")
                return f"Ошибка при входе: {e}", gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False)

        login_btn.click(
            on_login_click,
            inputs=[login_user, login_password],
            outputs=[login_status, authenticated, current_user_id, login_panel, main_panel]
        )

        def on_logout_click(auth_state):
            """
            Выход: сбрасываем состояние аутентификации и показываем login_panel.
            """
            logger.info("User logged out (manual logout)")
            # Очистим сессию (при желании можно и другие state очистить)
            return gr.update(False), gr.update(None), gr.update(visible=True), gr.update(visible=False)

        btn_logout.click(
            on_logout_click,
            inputs=[authenticated],
            outputs=[authenticated, current_user_id, login_panel, main_panel]
        )

    return interface
