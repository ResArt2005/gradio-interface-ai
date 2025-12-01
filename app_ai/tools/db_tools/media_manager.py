import uuid
from pathlib import Path
from .DBPostgresqlGradio import db

MEDIA_DIR = Path("/app/media")


def save_image(file_bytes: bytes, extension: str = "png") -> str:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.{extension}"
    file_path = MEDIA_DIR / filename

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return f"media/{filename}"


def save_image_path_to_db(user_id: int, path: str):
    sql = f"""
        UPDATE users
        SET avatar = '{path}'
        WHERE id = {user_id}
    """
    db.insert(sql)
