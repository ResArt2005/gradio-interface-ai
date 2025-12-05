# tools/dbpg/DB_messages.py
from typing import List, Dict, Any, Optional
from tools.dbpg.DBPostgresqlGradio import db
from tools.debug import logger
from sqlalchemy import text
import json

def create_session(user_id: int, user_ip: str | None = None, extra: dict | None = None) -> int:
    """
    Корректно создаёт запись в sessions и возвращает session_id.
    Работает через engine.begin() и RETURNING.
    """
    extra_json = json.dumps(extra) if extra is not None else None

    sql = text("""
        INSERT INTO sessions (user_id, user_ip, extra)
        VALUES (:user_id, :user_ip, :extra)
        RETURNING session_id;
    """)

    with db.engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "user_id": user_id,
                "user_ip": user_ip,
                "extra": extra_json
            }
        )
        session_id = result.scalar()  # <-- вот правильный способ
        logger.success(f"Created session: {session_id} for user_id={user_id}")
        return session_id

def save_message(chat_id: str, user_id: Optional[int], role: str, content: str, session_id: Optional[int] = None) -> None:
    """
    Сохранить сообщение в messages и атомарно увеличить msg_count в chats.
    Алгоритм:
      1) UPDATE chats SET msg_count = msg_count + 1 WHERE chat_id = '...'
         RETURNING msg_count - 1 AS next_order
      2) INSERT INTO messages (..., num_order, ...) VALUES (..., next_order, ...)
    Всё выполняется в одном SQL запросе (atomic via RETURNING).
    """
    # Защита минимальная: приводим chat_id к строке и экранируем одинарные кавычки в content
    chat_id_sql = f"'{chat_id}'"
    user_id_sql = "NULL" if user_id is None else str(user_id)
    session_id_sql = "NULL" if session_id is None else str(session_id)
    # Экранируем single quotes в content
    safe_content = content.replace("'", "''")

    sql = f"""
    WITH next_ord AS (
        UPDATE chats
        SET msg_count = msg_count + 1, updated_at = NOW()
        WHERE chat_id = {chat_id_sql}
        RETURNING (msg_count - 1) AS next_order
    )
    INSERT INTO messages (session_id, user_id, chat_id, num_order, role, content, timestamp)
    SELECT {session_id_sql}, {user_id_sql}, {chat_id_sql}, next_ord.next_order, '{role}', '{safe_content}', NOW()
    FROM next_ord;
    """
    db.insert(sql)
    logger.debug(f"Saved message role={role} for chat_id={chat_id} (session_id={session_id})")

def load_messages_for_chat(chat_id: str) -> List[Dict[str, Any]]:
    """
    Загрузить все сообщения для chat_id в порядке num_order ASC.
    Возвращает список словарей: { 'role': str, 'content': str, 'timestamp': str, 'num_order': int, 'msg_id': int }
    Если чат не найден — возвращает [].
    """
    sql = f"""
    SELECT msg_id, role, content, num_order, timestamp
    FROM messages
    WHERE chat_id = '{chat_id}'
    ORDER BY num_order ASC;
    """
    rows = db.select(sql)
    if not rows:
        return []
    results = []
    for msg_id, role, content, num_order, timestamp in rows:
        results.append({
            "msg_id": msg_id,
            "role": role,
            "content": content,
            "num_order": num_order,
            "timestamp": timestamp
        })
    return results

def load_messages_for_user_chats(chat_ids: List[str]) -> Dict[str, List[Dict[str,Any]]]:
    """
    Удобная обёртка: принимает список chat_id (строк) и возвращает dict {chat_id: [messages...] }
    """
    out = {}
    for cid in chat_ids:
        out[cid] = load_messages_for_chat(cid)
    return out
