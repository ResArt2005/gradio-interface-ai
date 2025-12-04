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
        # ВАЖНО: использую тот же connection URL формат, что и раньше
        self.connection_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
        self.engine = create_engine(self.connection_url)

    # БАЗОВЫЕ МЕТОДЫ

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
    # ВЫПОЛНЕНИЕ SQL-ФАЙЛА
    def execute_sql_file(self, relative_path: str):
        """Выполнить SQL-файл по относительному пути."""
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
      
    # Проверка, какие таблицы есть в базе
    def check_tables(self):
        sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        tables = self.select_as_dict(sql)
        logger.info(f"Таблицы в БД: {[t['table_name'] for t in tables]}")

    # Рекурсивное извлечение дерева быстрых запросов
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
    # Загрузка JSON файла дерева быстрых запросов в таблицу
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
