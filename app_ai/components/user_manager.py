import gradio as gr
from tools.dbpg.DB_users import replace_user_avatar, get_user_avatar_path, change_user_fio, change_user_email, is_uniqe_email, verify_password_hash, save_password, get_user_by_id
from tools.debug import logger

def on_avatar_change(file: str, user_id: int):
    if not user_id:
        return None, "Ошибка: пользователь не авторизован"

    # --- Если файл загружен ---
    if file:
        try:
            # file — это строка: "/tmp/gradio/uploaded_image.png"
            with open(file, "rb") as f:
                file_bytes = f.read()

            ext = file.split(".")[-1].lower()

            new_path = replace_user_avatar(user_id, file_bytes, ext)

            logger.info("Аватар обновлён для user_id=%s -> %s", user_id, new_path)

            return f"/app/{new_path}", "Аватар обновлён!"

        except Exception as e:
            logger.error("Ошибка при сохранении аватара: %s", e)
            return None, f"Ошибка при сохранении: {e}"

    # --- Если файл НЕ выбран ---
    current = get_user_avatar_path(user_id)
    return (f"/app/{current}" if current else None), "Аватар не выбран"

def fio_change(first_name: str, last_name: str, surname:str, user_id: int):
    if not user_id:
        return gr.update(''), gr.update(''), gr.update(''), "Ошибка: пользователь не авторизован"
    # Логика обновления ФИО в базе данных
    if not first_name or not last_name:
        return gr.update(''), gr.update(''), gr.update(''), "Ошибка: Имя и Фамилия обязательны"
    change_user_fio(user_id, first_name, last_name, surname)
    logger.info("ФИО обновлено для user_id=%s -> %s", user_id, f"{last_name} {first_name} {surname if surname else ''}")
    return gr.update(first_name), gr.update(last_name), gr.update(surname), "Актуальное ФИО сохранено"

def email_change(e_mail: str, user_id: int):
    if not user_id:
        return gr.update(''), "Ошибка: пользователь не авторизован"
    if not e_mail or "@" not in e_mail:
        return gr.update(''), "Ошибка: Некорректный email"
    if is_uniqe_email(e_mail, user_id) is False:
        return gr.update(''), "Ошибка: Этот email уже используется"
    change_user_email(user_id, e_mail)
    logger.info("Email обновлен для user_id=%s -> %s", user_id, e_mail)
    return gr.update(e_mail), "Актуальный email сохранен"

def password_change(current_password: str, new_password: str, confirm_new_password_txt:str, user_id: int):
    if not user_id:
        return "Ошибка: пользователь не авторизован", '', '', ''
    user = get_user_by_id(user_id)
    if not user:
        return "Ошибка: пользователь не найден", '', '', ''
    
    if not verify_password_hash(current_password, user['password_hash']):
        return "Ошибка: Текущий пароль неверен", current_password, new_password, confirm_new_password_txt
    if len(new_password) < 6:
        return "Ошибка: Новый пароль должен быть не менее 6 символов", current_password, new_password, confirm_new_password_txt
    if new_password != confirm_new_password_txt:
        return "Ошибка: Новый пароль и подтверждение не совпадают", current_password, new_password, confirm_new_password_txt
    save_password(user_id, new_password)
    logger.info("Пароль обновлен для user_id=%s", user_id)
    return "Пароль успешно изменен", '', '', ''

def open_settings_panel():
    return gr.update(visible=False), gr.update(visible=True)

def back_to_main_panel():
    return gr.update(visible=True), gr.update(visible=False), ''