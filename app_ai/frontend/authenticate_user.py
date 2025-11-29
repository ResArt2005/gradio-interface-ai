from ui.UI import UI
import gradio as gr
def authenticate_user(ui: UI):
    ui.authenticated = gr.State(False)
    ui.current_user_id = gr.State(None)

    with gr.Column(visible=True, elem_id="login_panel") as ui.login_panel:
        gr.Markdown("### Вход")
        ui.login_user = gr.Textbox(label="Логин", placeholder="Введите логин", lines=1)
        ui.login_password = gr.Textbox(label="Пароль", placeholder="Введите пароль", type="password")
        ui.login_btn = gr.Button(value="Войти")
        ui.login_status = gr.Text(value="", interactive=False)