import gradio as gr
from tools.dbpg.DB_users import replace_user_avatar, get_user_avatar_path, change_user_fio, change_user_email, is_uniqe_email, verify_password_hash, save_password, get_user_by_id
from tools.debug import logger
from PIL import Image
from io import BytesIO

SIZE = 5
MAX_AVATAR_SIZE = SIZE * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

class AvatarValidationError(Exception):
    pass

def validate_and_sanitize_image(file_bytes: bytes, extension: str) -> bytes:
    # --- Размер ---
    if len(file_bytes) > MAX_AVATAR_SIZE:
        raise AvatarValidationError(f"Файл превышает {SIZE} МБ")

    # --- Расширение ---
    ext = extension.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AvatarValidationError("Допустимы только PNG и JPG")

    # --- Проверка, что это реально изображение ---
    try:
        with Image.open(BytesIO(file_bytes)) as img:
            img.verify()  # проверка целостности
    except Exception:
        raise AvatarValidationError("Файл не является корректным изображением")

    # --- Повторно открываем (verify закрывает поток) ---
    with Image.open(BytesIO(file_bytes)) as img:
        img = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img

        # --- Пересохранение (УБИВАЕТ вредоносный код) ---
        output = BytesIO()
        if ext in ("jpg", "jpeg"):
            img.save(output, format="JPEG", quality=95, optimize=True)
        else:
            img.save(output, format="PNG", optimize=True)

        return output.getvalue()

def on_avatar_change(file: str, user_id: int):
    if not user_id:
        return None, "Ошибка: пользователь не авторизован"

    if file:
        try:
            with open(file, "rb") as f:
                raw_bytes = f.read()

            ext = file.split(".")[-1].lower()

            safe_bytes = validate_and_sanitize_image(raw_bytes, ext)

            new_path = replace_user_avatar(user_id, safe_bytes, ext)

            logger.info("Аватар обновлён для user_id=%s -> %s", user_id, new_path)
            return f"/app/{new_path}", "Аватар обновлён!"

        except AvatarValidationError as e:
            logger.warning("Невалидный аватар: %s", e)
            current = get_user_avatar_path(user_id)
            return (f"/app/{current}" if current else None), str(e)

        except Exception as e:
            logger.error("Ошибка при сохранении аватара: %s", e)
            current = get_user_avatar_path(user_id)
            return (f"/app/{current}" if current else None), f"Ошибка при сохранении: {e}"

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