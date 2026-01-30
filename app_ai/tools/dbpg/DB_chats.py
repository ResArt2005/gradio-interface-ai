import datetime
import json
from tools.dbpg.DBPostgresqlGradio import db
from tools.debug import logger
from typing import Dict
def save_new_chat(chat_id: str, title: str, user_id: int) -> None:
    """Save a new chat to the database."""
    query = f"""
    INSERT INTO chats (chat_id, title, user_id, created_at, updated_at, msg_count)
    VALUES ('{chat_id}', '{title}', {user_id}, NOW(), NOW(), 0);
    """
    db.insert(query)
    logger.info(f"New chat saved to database with chat_id: {chat_id}")

def delete_chat_from_bd(chat_id: str) -> None:
    """Delete a chat from the database."""
    query = f"UPDATE chats SET chat_state='deleted' WHERE chat_id = '{chat_id}';"
    db.insert(query)
    logger.info(f"Chat deleted from database with chat_id: {chat_id}")

def rename_chat_in_bd(chat_id: str, new_title: str) -> None:
    """Rename an existing chat."""
    query = f"""
    UPDATE chats
    SET title = '{new_title}', updated_at = NOW()
    WHERE chat_id = '{chat_id}';
    """
    db.insert(query)
    logger.info(f"Chat renamed to '{new_title}' in database with chat_id: {chat_id}")

def download_chats_for_user(user_id: int) -> Dict[str, str]:
    """Download all chats for a specific user."""
    query = f"SELECT chat_id, title FROM chats WHERE user_id = {user_id} and chat_state='active' ORDER BY updated_at DESC;"
    rows = db.select(query)
    return {str(row[0]): row[1] for row in rows} if rows else {}

def append_chat_log(chat_id: str, log: dict) -> None:
    # always include a timestamp if not present
    if "time" not in log:
        log["time"] = datetime.utcnow().isoformat() # datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        UPDATE chats
        SET chat_logs = COALESCE(chat_logs, '[]'::jsonb) ||
                        to_jsonb(CAST(:entry AS json)),
            updated_at = NOW()
        WHERE chat_id = :cid;
    """

    params = {
        "cid": chat_id,
        # IMPORTANT: pass JSON as a string, not a dict
        "entry": json.dumps(log, ensure_ascii=False)
    }

    # execute directly via engine to ensure parameters are passed exactly
    db.insert(sql, params)

    logger.debug(f"Appended log to chat {chat_id}: {log}")