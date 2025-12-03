from ui.UI import UI
import gradio as gr
def authenticate_user(ui: UI):
    with gr.Column(visible=True, elem_id="login_panel") as ui.login_panel:
        gr.Markdown("### Вход")
        ui.login_user = gr.Textbox(label="Логин", placeholder="Введите логин", lines=1)
        ui.login_password = gr.Textbox(label="Пароль", placeholder="Введите пароль", type="password")
        ui.login_btn = gr.Button(value="Войти")
        ui.login_status = gr.Text(value="", interactive=False)

def logout_user(ui: UI):
    with gr.Row():
        ui.btn_logout = gr.Button(value="Выйти", variant="secondary", elem_id="btn_logout")
        gr.Markdown("")

def open_settings_panel(ui: UI):
    with gr.Row():
        ui.open_settings_btn = gr.Button(value="Открыть настройки", variant="secondary", elem_id="btn_open_settings")
        gr.Markdown("")
