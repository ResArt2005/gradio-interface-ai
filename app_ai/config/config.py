from dotenv import load_dotenv
import os

# Загружаем .env
load_dotenv()

class Config:
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    API_KEY = os.getenv("API_KEY")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
