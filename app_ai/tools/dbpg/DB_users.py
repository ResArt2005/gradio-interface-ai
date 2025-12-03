import uuid
from pathlib import Path
from tools.dbpg.DBPostgresqlGradio import db
MEDIA_DIR = Path("/app/media")

# Получение IP адреса пользователя
def save_client_ip(user_id: int, ip: str) -> None:
    sql = f"""
        UPDATE users
        SET user_ip_address = '{ip}'
        WHERE user_id = {user_id};
    """
    db.insert(sql)


# Работа с аватарами пользователей

def save_image(file_bytes: bytes, extension: str = "png") -> str:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.{extension}"
    file_path = MEDIA_DIR / filename

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # возвращаем относительный путь, который храним в БД
    return f"media/{filename}"


def get_user_avatar_path(user_id: int) -> str | None:
    sql = f"""
        SELECT avatar
        FROM users
        WHERE user_id = {user_id};
    """
    result = db.select(sql)
    if result and result[0][0]:
        return result[0][0]
    return None


def delete_avatar_from_disk(path: str | None):
    """Удалить физический файл, если указан путь и файл существует."""
    if not path:
        return
    filepath = Path("/app") / path
    if filepath.exists():
        try:
            filepath.unlink()
        except Exception:
            # логгирование можно добавить при необходимости
            pass


def save_image_path_to_db(user_id: int, path: str | None):
    """Обновить поле avatar в БД (может устанавливать NULL)."""
    if path is None:
        sql = f"UPDATE users SET avatar = NULL WHERE user_id = {user_id};"
    else:
        sql = f"UPDATE users SET avatar = '{path}' WHERE user_id = {user_id};"
    db.insert(sql)


def replace_user_avatar(user_id: int, new_file_bytes: bytes | None, extension: str | None = "png") -> str | None:
    """
    Универсальная функция:
    - если new_file_bytes is None -> ничего не сохраняет, возвращает текущий путь
    - иначе: удаляет старый файл (если есть), сохраняет новый, обновляет БД и возвращает новый путь
    """
    if new_file_bytes is None:
        return get_user_avatar_path(user_id)

    # удаляем старый файл
    old_path = get_user_avatar_path(user_id)
    if old_path:
        delete_avatar_from_disk(old_path)

    # сохраняем новый
    new_path = save_image(new_file_bytes, extension or "png")
    save_image_path_to_db(user_id, new_path)

    return new_path

# Работа с ФИО пользователя
def get_user_fio(user_id: int) -> tuple[str, str, str | None]:
    """Получить ФИО пользователя из базы данных."""
    sql = f"""
        SELECT first_name, last_name, surname
        FROM users
        WHERE user_id = {user_id};
    """
    result = db.select(sql)
    if result:
        first_name, last_name, surname = result[0]
        return first_name, last_name, surname if surname else ""
    return "", "", ""

def change_user_fio(user_id: int, first_name: str, last_name: str, surname: str | None = None):
    """Обновить ФИО пользователя в базе данных."""
    sql = f"""
        UPDATE users
        SET first_name = '{first_name}', last_name = '{last_name}', surname = '{surname if surname else ''}'
        WHERE user_id = {user_id};
    """
    db.insert(sql)