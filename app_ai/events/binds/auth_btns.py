from ui.UI import UI
from events.events import ( on_login_click, on_logout_click )

def auth_btns(ui: UI):
    """Привязка событий для кнопок аутентификации."""
    #  LOGIN
    ui.login_btn.click(
        on_login_click,
        inputs=[ui.login_user, ui.login_password],
        outputs=[
            ui.login_status,
            ui.authenticated,
            ui.current_user_id,
            ui.login_panel,
            ui.main_panel,
            ui.avatar_preview
        ]
    )
    #  LOGOUT
    ui.btn_logout.click(
        on_logout_click,
        inputs=[ui.authenticated],
        outputs=[
            ui.authenticated,
            ui.current_user_id,
            ui.login_panel,
            ui.main_panel,
            ui.avatar_preview,
            ui.avatar_upload
        ]
    )