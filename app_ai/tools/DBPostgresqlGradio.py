from sqlalchemy import create_engine, text
import pandas as pd
import io
from config.config import Config
from sqlalchemy.exc import SQLAlchemyError
from tools.debug import logger
class DBPostgresqlGradio:
    """sqlalchemy, psycopg[binary] - MIT License"""

    def __init__(self, dbname: str, user: str, password: str, host: str, port: int):
        self.connection_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
        self.engine = create_engine(self.connection_url)

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

    def insert_many(self, table: str, columns: list[str], data: list[tuple]):
        """Массовая вставка через SQLAlchemy."""
        df = pd.DataFrame(data, columns=columns)
        df.to_sql(table, self.engine, if_exists="append", index=False)

    def insert_dataframe(self, schema: str, table: str, df: pd.DataFrame):
        """Вставка DataFrame в таблицу."""
        df.to_sql(table, self.engine, schema=schema, if_exists="append", index=False)

    def select_as_dict(self, sql: str):
        """Выполнить SELECT и вернуть список словарей."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result.fetchall()]

    def copy_from_dataframe(self, schema: str, table: str, df: pd.DataFrame):
        """
        Быстрая загрузка данных из DataFrame (через COPY-like механизм)
        """
        df.to_sql(table, self.engine, schema=schema, if_exists="append", index=False, method="multi")


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
