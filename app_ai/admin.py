#!/usr/bin/env python3
"""
admin.py

Usage (Windows):
  admin.bat add-user <username> <password>
  admin.bat remove-user <username>

Direct usage:
  python admin.py add-user alice secret123
  python admin.py remove-user alice

Примечания:
 - По умолчанию подключается к БД:
     host=localhost, port=5433, user=postgres, password=postgres, dbname=gradioBD
 - Можно переопределить через переменные окружения:
     PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
 - Требуемые пакеты: sqlalchemy, psycopg2-binary, bcrypt, python-dotenv (опционально)
"""
from config.config import Config
import sys
import getpass
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- Конфигурация по умолчанию (под Docker compose из твоего примера) ---
PGHOST = Config.DB_HOST
#PGPORT = Config.DB_PORT
PGPORT = 5433
PGUSER = Config.DB_USER
PGPASSWORD = Config.DB_PASSWORD
PGDATABASE = Config.DB_NAME

DB_URL = f"postgresql+psycopg://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

# --- Создаём engine SQLAlchemy ---
engine = create_engine(DB_URL, pool_size=5, max_overflow=10, future=True)


def hash_password(plain_password: str) -> str:
    """Возвращает bcrypt-хэш (utf-8 строка)."""
    pw = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(pw, bcrypt.gensalt())
    return hashed.decode("utf-8")


def add_user(username: str, password: str) -> int:
    """Добавляет пользователя, возвращает его id. Если уже есть — выбрасывает ValueError."""
    # проверка параметров
    if not username:
        raise ValueError("username is empty")
    if not password:
        raise ValueError("password is empty")

    password_hash = hash_password(password)
    with engine.begin() as conn:
        # сначала проверим, нет ли такого username
        r = conn.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": username}
        ).first()
        if r is not None:
            raise ValueError(f"User '{username}' already exists (id={r[0]}).")

        # вставим запись
        res = conn.execute(
            text(
                """
                INSERT INTO users (username, password_hash)
                VALUES (:username, :password_hash)
                RETURNING id;
                """
            ),
            {"username": username, "password_hash": password_hash}
        ).first()
        user_id = res[0]
        print(f"Created user '{username}' with id={user_id}")
        return user_id


def remove_user(username: str) -> None:
    """Удаляет пользователя и все связанные сущности (через ON DELETE CASCADE)."""
    if not username:
        raise ValueError("username is empty")
    with engine.begin() as conn:
        r = conn.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": username}
        ).first()
        if r is None:
            raise ValueError(f"User '{username}' does not exist.")
        user_id = r[0]

        # для безопасности — можно вывести сколько записей удалится (опционально)
        # считаем кол-во чатов и сообщений (в транзакции)
        sessions_count = conn.execute(
            text("SELECT COUNT(*) FROM chat_sessions WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).scalar_one()
        messages_count = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM chat_messages cm
                JOIN chat_sessions cs ON cm.session_id = cs.id
                WHERE cs.user_id = :user_id
                """
            ),
            {"user_id": user_id}
        ).scalar_one()

        print(f"About to remove user '{username}' (id={user_id}).")
        print(f"  chat_sessions to be removed: {sessions_count}")
        print(f"  chat_messages to be removed: {messages_count}")

        # Подтверждение — это полезно, можно пропустить в автоматическом режиме
        answer = input("Confirm deletion (type 'yes' to proceed): ").strip().lower()
        if answer != "yes":
            print("Aborted by user.")
            return

        # удаляем
        conn.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        print(f"User '{username}' (id={user_id}) and related data removed.")


def print_help():
    print("Usage:")
    print("  admin.py add-user <username> <password>")
    print("  admin.py remove-user <username>")
    print("")
    print("Environment variables to override DB connection:")
    print("  PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE")
    print("")
    print("Examples:")
    print("  python admin.py add-user alice secret123")
    print("  python admin.py remove-user alice")


def main(argv):
    if len(argv) < 2:
        print_help()
        return 1

    cmd = argv[1]
    try:
        if cmd == "add-user":
            if len(argv) == 4:
                username = argv[2]
                password = argv[3]
            elif len(argv) == 3:
                username = argv[2]
                # спрашиваем пароль интерактивно
                password = getpass.getpass("Password: ")
            else:
                print("add-user requires <username> <password>")
                return 2
            add_user(username, password)
            return 0

        elif cmd == "remove-user":
            if len(argv) != 3:
                print("remove-user requires <username>")
                return 2
            username = argv[2]
            remove_user(username)
            return 0

        else:
            print(f"Unknown command: {cmd}")
            print_help()
            return 2

    except ValueError as ve:
        print("Error:", ve)
        return 3
    except SQLAlchemyError as sqle:
        print("Database error:", str(sqle))
        return 4
    except Exception as e:
        print("Unexpected error:", str(e))
        return 5


if __name__ == "__main__":
    sys.exit(main(sys.argv))
