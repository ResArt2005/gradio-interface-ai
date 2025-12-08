from tools.dbpg.DBPostgresqlGradio import db
from tools.debug import logger
from typing import Optional, Dict, Any

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
    query = f"UPDATE chats SET chat_state='disabled' WHERE chat_id = '{chat_id}';"
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
    query = f"SELECT chat_id, title FROM chats WHERE user_id = {user_id} and chat_state='active';"
    rows = db.select(query)
    return {str(row[0]): row[1] for row in rows} if rows else {}