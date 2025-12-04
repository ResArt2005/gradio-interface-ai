import uuid
from pathlib import Path
from tools.dbpg.DBPostgresqlGradio import db
from tools.debug import logger
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
# Добавляем bcrypt для хэширования паролей
import bcrypt
from typing import Optional, Dict, Any
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

# Работа с email пользователя
def get_user_email(user_id: int) -> str | None:
    """Получить email пользователя из базы данных."""
    sql = f"""
        SELECT e_mail
        FROM users
        WHERE user_id = {user_id};
    """
    result = db.select(sql)
    if result and result[0][0]:
        return result[0][0]
    return ''

def change_user_email(user_id: int, new_email: str):
    """Обновить email пользователя в базе данных."""
    sql = f"""
        UPDATE users
        SET e_mail = '{new_email}'
        WHERE user_id = {user_id};
    """
    db.insert(sql)

def is_uniqe_email(email: str, user_id: int) -> bool:
    """Проверить, что e_mail уникален среди всех пользователей, кроме текущего."""
    sql = f"""
        SELECT COUNT(*)
        FROM users
        WHERE e_mail = '{email}' AND user_id != {user_id};
    """
    result = db.select(sql)
    if result and result[0][0] == 0:
        return True
    return False

# МЕТОДЫ ДЛЯ АУТЕНТИФИКАЦИИ И УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ
def hash_password(plain_password: str) -> str:
    if isinstance(plain_password, str):
        plain_password = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(plain_password, bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password_hash(plain_password: str, password_hash: str) -> bool:
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode("utf-8")
        if isinstance(password_hash, str):
            password_hash = password_hash.encode("utf-8")
        return bcrypt.checkpw(plain_password, password_hash)
    except Exception as e:
        logger.error(f"verify_password_hash error: {e}")
        return False

def save_password(user_id: int, plain_password: str):
    password_hash = hash_password(plain_password)
    sql = f"""
        UPDATE users
        SET password_hash = '{password_hash}'
        WHERE user_id = {user_id};
    """
    db.insert(sql)

# ----- CRUD для пользователей -----
def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    sql = text("SELECT user_id, username, password_hash, created_at, last_login FROM users WHERE username = :username")
    with db.engine.connect() as conn:
        res = conn.execute(sql, {"username": username}).mappings().first()
        if res:
            return dict(res)
        return None
def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    sql = text("SELECT user_id, username, password_hash, created_at, last_login FROM users WHERE user_id = :user_id")
    with db.engine.connect() as conn:
        res = conn.execute(sql, {"user_id": user_id}).mappings().first()
        if res:
            return dict(res)
        return None
def create_user(username: str, plain_password: str) -> int:
    password_hash = hash_password(plain_password)
    sql_check = text("SELECT user_id FROM users WHERE username = :username")
    sql_insert = text("""
        INSERT INTO users (username, password_hash)
        VALUES (:username, :password_hash)
        RETURNING user_id
    """)
    with db.engine.begin() as conn:
        exists = conn.execute(sql_check, {"username": username}).first()
        if exists:
            raise ValueError(f"User '{username}' already exists (user_id={exists[0]}).")
        res = conn.execute(sql_insert, {"username": username, "password_hash": password_hash}).first()
        user_id = res[0]
        logger.info(f"Created user '{username}' id={user_id}")
        return user_id

def remove_user_by_username(username: str) -> None:
    """
    Удаляет пользователя по username. Благодаря ON DELETE CASCADE удалятся связанные чаты/сообщения.
    """
    sql = text("DELETE FROM users WHERE username = :username")
    with db.engine.begin() as conn:
        conn.execute(sql, {"username": username})
        logger.info(f"Removed user '{username}' (if existed).")

def verify_user_credentials(username: str, plain_password: str) -> Optional[int]:
    user = get_user_by_username(username)
    if not user:
        logger.debug(f"verify_user_credentials: user '{username}' not found")
        return None
    if not user.get("password_hash"):
        logger.warning(f"User {username} has no password_hash stored")
        return None
    ok = verify_password_hash(plain_password, user["password_hash"])
    if ok:
        return user["user_id"]
    return None

def update_last_login(user_id: int):
    sql = text("UPDATE users SET last_login = NOW() WHERE user_id = :user_id")
    with db.engine.begin() as conn:
        conn.execute(sql, {"user_id": user_id})
        logger.info(f"Updated last_login for user_id={user_id}")
