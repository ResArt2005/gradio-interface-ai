from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from pathlib import Path
import json
from config.config import Config
from tools.debug import logger


class DBPostgresqlGradio:
    """sqlalchemy + psycopg[binary] — MIT License"""

    BASE_DIR = Path(__file__).parent

    def __init__(self, dbname: str, user: str, password: str, host: str, port: int):
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
    # 🔹 2. РЕКУРСИВНОЕ ИЗВЛЕЧЕНИЕ ДЕРЕВА
    # ===============================================================

    def get_tree_as_json(self):
        """
        Извлекает дерево из таблицы tree_nodes и возвращает его в виде JSON:
        только {"name": ..., "children": [...]} без id и parent_id.
        """
        sql = """
        SELECT id, name, parent_id
        FROM prompt_tree
        ORDER BY id;
        """
        nodes = self.select_as_dict(sql)

        # Создаем словарь всех узлов {id: {"name": ..., "children": []}}
        node_map = {n["id"]: {"name": n["name"], "children": []} for n in nodes}

        # Собираем дерево
        for n in nodes:
            parent_id = n["parent_id"]
            if parent_id:
                # Добавляем текущий узел в children родителя
                node_map[parent_id]["children"].append(node_map[n["id"]])

        # Корневые узлы — это те, у которых parent_id is None
        root_nodes = [node_map[n["id"]] for n in nodes if n["parent_id"] is None]

        return root_nodes

    # ===============================================================
    # 🔹 3. ЗАГРУЗКА JSON-ФАЙЛА В ТАБЛИЦУ
    # ===============================================================

    def load_json_to_tree(self, relative_json_path: str):
        """
        Загружает JSON дерево в таблицу prompt_tree.
        Пример: db.load_json_to_tree('data/tree.json')
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
                node_id = insert_node(conn, item["name"], parent_id)
                if item.get("children"):
                    insert_children(conn, item["children"], node_id)

        try:
            with self.engine.begin() as conn:
                insert_children(conn, data)
            logger.success(f"JSON дерево успешно загружено из {relative_json_path}")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при загрузке JSON дерева: {e}")
            raise

try:
    db = DBPostgresqlGradio(
        Config.DB_NAME,
        Config.DB_USER,
        Config.DB_PASSWORD,
        Config.DB_HOST,
        Config.DB_PORT
    )
    logger.success("Подключение к PostgreSQL успешно установлено.")
except SQLAlchemyError as e:
    logger.error(f"Ошибка SQLAlchemy: {e}")
    db = None
except Exception as e:
    logger.error(f"Неизвестная ошибка: {e}")
    db = None

#db.execute_sql_file("sql/create_prompt_tree.sql")
#db.load_json_to_tree("json/prompt_tree.json")
#print(db.get_tree_as_json())