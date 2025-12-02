# tools/DBPostgresqlGradio.py
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from pathlib import Path
import json
from config.config import Config
from tools.debug import logger

# Добавляем bcrypt для хэширования паролей
import bcrypt
from typing import Optional, Dict, Any

class DBPostgresqlGradio:
    """sqlalchemy + psycopg[binary] — MIT License"""

    BASE_DIR = Path(__file__).parent

    def __init__(self, dbname: str, user: str, password: str, host: str, port: int):
        # ВАЖНО: использую тот же connection URL формат, что и раньше
        self.connection_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
        self.engine = create_engine(self.connection_url)

    # ===============================================================
    # 🔹 БАЗОВЫЕ МЕТОДЫ
    # ===============================================================

    def select(self, sql: str):
        """Выполнить SELECT и вернуть список кортежей."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            return [tuple(row) for row in result.fetchall()]

    def select_dataframe(self, sql: str):
        """Выполнить SELECT и вернуть pandas DataFrame."""
        return pd.read_sql(sql, self.engine)

    def insert(self, sql: str):
        """Выполнить INSERT/UPDATE/DELETE."""
        with self.engine.begin() as conn:
            conn.execute(text(sql))

    def execute_without_transaction(self, sql: str):
        """Выполнить SQL без транзакции (автокоммит)."""
        with self.engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(text(sql))

    def select_as_dict(self, sql: str):
        """Выполнить SELECT и вернуть список словарей."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result.fetchall()]

    # ===============================================================
    # 🔹 0. НОВЫЕ МЕТОДЫ ДЛЯ АУТЕНТИФИКАЦИИ / ПОЛЬЗОВАТЕЛЕЙ
    # ===============================================================

    # ----- Вспомогательные функции хэширования -----
    def hash_password(self, plain_password: str) -> str:
        """
        Хэширует пароль с помощью bcrypt и возвращает строковый хэш (utf-8).
        """
        if isinstance(plain_password, str):
            plain_password = plain_password.encode("utf-8")
        hashed = bcrypt.hashpw(plain_password, bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify_password_hash(self, plain_password: str, password_hash: str) -> bool:
        """
        Проверяет plain_password против password_hash.
        Возвращает True/False.
        """
        try:
            if isinstance(plain_password, str):
                plain_password = plain_password.encode("utf-8")
            if isinstance(password_hash, str):
                password_hash = password_hash.encode("utf-8")
            return bcrypt.checkpw(plain_password, password_hash)
        except Exception as e:
            logger.error(f"verify_password_hash error: {e}")
            return False

    # ----- CRUD для пользователей -----
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает запись пользователя как словарь: user_id, username, password_hash, created_at, last_login
        Или None, если пользователь не найден.
        """
        sql = text("SELECT user_id, username, password_hash, created_at, last_login FROM users WHERE username = :username")
        with self.engine.connect() as conn:
            res = conn.execute(sql, {"username": username}).mappings().first()
            if res:
                return dict(res)
            return None

    def create_user(self, username: str, plain_password: str) -> int:
        """
        Создаёт пользователя в таблице users (хэширует пароль).
        Возвращает user_id нового пользователя.
        """
        password_hash = self.hash_password(plain_password)
        sql_check = text("SELECT user_id FROM users WHERE username = :username")
        sql_insert = text("""
            INSERT INTO users (username, password_hash)
            VALUES (:username, :password_hash)
            RETURNING user_id
        """)
        with self.engine.begin() as conn:
            exists = conn.execute(sql_check, {"username": username}).first()
            if exists:
                raise ValueError(f"User '{username}' already exists (user_id={exists[0]}).")
            res = conn.execute(sql_insert, {"username": username, "password_hash": password_hash}).first()
            user_id = res[0]
            logger.info(f"Created user '{username}' id={user_id}")
            return user_id

    def remove_user_by_username(self, username: str) -> None:
        """
        Удаляет пользователя по username. Благодаря ON DELETE CASCADE удалятся связанные чаты/сообщения.
        """
        sql = text("DELETE FROM users WHERE username = :username")
        with self.engine.begin() as conn:
            conn.execute(sql, {"username": username})
            logger.info(f"Removed user '{username}' (if existed).")

    def verify_user_credentials(self, username: str, plain_password: str) -> Optional[int]:
        """
        Проверяет логин/пароль. Если валидно — возвращает user_id, иначе None.
        """
        user = self.get_user_by_username(username)
        if not user:
            logger.debug(f"verify_user_credentials: user '{username}' not found")
            return None
        if not user.get("password_hash"):
            logger.warning(f"User {username} has no password_hash stored")
            return None
        ok = self.verify_password_hash(plain_password, user["password_hash"])
        if ok:
            return user["user_id"]
        return None

    def update_last_login(self, user_id: int):
        """
        Обновляет поле last_login для пользователя (NOW()).
        """
        sql = text("UPDATE users SET last_login = NOW() WHERE user_id = :user_id")
        with self.engine.begin() as conn:
            conn.execute(sql, {"user_id": user_id})
            logger.info(f"Updated last_login for user_id={user_id}")

    # ===============================================================
    # 🔹 1. ВЫПОЛНЕНИЕ SQL-ФАЙЛА
    # ===============================================================

    def execute_sql_file(self, relative_path: str):
        """
        Выполнить SQL-файл по относительному пути.
        Пример: db.execute_sql_file('sql/init_tree_table.sql')
        """
        sql_path = self.BASE_DIR / relative_path
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL файл не найден: {sql_path}")

        with open(sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        try:
            with self.engine.begin() as conn:
                conn.execute(text(sql_script))
            logger.success(f"SQL файл выполнен успешно: {relative_path}")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при выполнении SQL файла {relative_path}: {e}")
            raise

    # ===============================================================
    # 🔹 2. РЕКУРСИВНОЕ ИЗВЛЕЧЕНИЕ ДЕРЕВА (оставлено без изменений)
    # ===============================================================
    def check_tables(self):
        sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        tables = self.select_as_dict(sql)
        logger.info(f"Таблицы в БД: {[t['table_name'] for t in tables]}")

    def get_tree_as_json(self):
        """
        Извлекает дерево из таблицы tree_nodes и возвращает его в виде JSON:
        только {"name": ..., "children": [...]} без id и parent_id.
        Рекурсивно строит дерево любой глубины.
        """
        sql = """
        WITH RECURSIVE tree_paths AS (
            -- Корневые узлы
            SELECT 
                id,
                name,
                parent_id,
                ARRAY[id] as path,
                1 as level
            FROM public.prompt_tree 
            WHERE parent_id IS NULL
            
            UNION ALL
            
            -- Дочерние узлы
            SELECT 
                t.id,
                t.name,
                t.parent_id,
                tp.path || t.id,
                tp.level + 1
            FROM public.prompt_tree t
            JOIN tree_paths tp ON t.parent_id = tp.id
        )
        SELECT 
            id,
            name,
            parent_id,
            path,
            level
        FROM tree_paths
        ORDER BY path;
        """
        
        nodes = self.select_as_dict(sql)
        
        # Создаем словарь для быстрого доступа к узлам по id
        node_map = {}
        for node in nodes:
            node_map[node['id']] = {
                'name': node['name'],
                'children': [],
                'level': node['level']
            }
        
        # Сортируем узлы по уровню (от самого глубокого к корневому)
        # чтобы гарантировать, что дочерние узлы будут добавлены перед родительскими
        sorted_nodes = sorted(nodes, key=lambda x: x['level'], reverse=True)
        
        # Строим дерево снизу вверх
        root_nodes = []
        for node in sorted_nodes:
            current_node = node_map[node['id']]
            
            if node['parent_id'] is None:
                # Это корневой узел
                root_nodes.append({
                    'name': current_node['name'],
                    'children': current_node['children']
                })
            else:
                # Это дочерний узел - добавляем его к родителю
                parent_node = node_map.get(node['parent_id'])
                if parent_node:
                    parent_node['children'].append({
                        'name': current_node['name'],
                        'children': current_node['children']
                    })
        
        # Корневые узлы должны быть в правильном порядке
        root_nodes.reverse()
        return root_nodes

    # ===============================================================
    # 🔹 3. ЗАГРУЗКА JSON-ФАЙЛА В ТАБЛИЦУ
    # ===============================================================
    def load_json_to_tree(self, relative_json_path: str):
        """
        Загружает JSON дерево в таблицу prompt_tree.
        Пример: db.load_json_to_tree('data/tree.json')
        Рекурсивно обрабатывает дерево любой глубины.
        """
        json_path = self.BASE_DIR / relative_json_path
        if not json_path.exists():
            raise FileNotFoundError(f"JSON файл не найден: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        def insert_node(conn, name, parent_id=None):
            sql = text("""
                INSERT INTO prompt_tree (name, parent_id)
                VALUES (:name, :parent_id)
                RETURNING id;
            """)
            result = conn.execute(sql, {"name": name, "parent_id": parent_id})
            return result.scalar()

        def insert_children(conn, items, parent_id=None):
            for item in items:
                # Вставляем текущий узел
                node_id = insert_node(conn, item["name"], parent_id)
                
                # Рекурсивно вставляем детей, если они есть
                if "children" in item and item["children"]:
                    insert_children(conn, item["children"], node_id)

        try:
            # Очищаем таблицу перед загрузкой нового дерева
            with self.engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE prompt_tree RESTART IDENTITY CASCADE;"))
                # Вставляем новое дерево
                insert_children(conn, data)
            logger.success(f"JSON дерево успешно загружено из {relative_json_path}")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при загрузке JSON дерева: {e}")
            raise

# ---------------------------------------------------------------------
# НИЖЕ (в твоём файле) у тебя уже был код для инициализации экземпляра db.
# Я оставляю это поведение — он создаёт объект db и вызывает check_tables.
# ---------------------------------------------------------------------
try:
    db = DBPostgresqlGradio(
        Config.DB_NAME,
        Config.DB_USER,
        Config.DB_PASSWORD,
        Config.DB_HOST,
        Config.DB_PORT
    )
    logger.success("Подключение к PostgreSQL успешно установлено.")
    db.check_tables()
except SQLAlchemyError as e:
    logger.error(f"Ошибка SQLAlchemy: {e}")
    db = None
except Exception as e:
    logger.error(f"Неизвестная ошибка: {e}")
    db = None

# Инициализация таблицы и загрузка данных
#db.execute_sql_file("sql/create_prompt_tree.sql")
#db.load_json_to_tree("json/prompt_tree.json")
# print(db.get_tree_as_json())
