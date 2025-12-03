import uuid
from pathlib import Path
from tools.dbpg.DBPostgresqlGradio import db
MEDIA_DIR = Path("/app/media")


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

