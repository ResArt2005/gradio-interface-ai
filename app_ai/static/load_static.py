from pathlib import Path
from tools.debug import logger
BASE_DIR = Path(__file__).parent.parent

def load_file(relative_path: str) -> str:
    """Универсальная функция загрузки файлов"""
    try:
        with open(BASE_DIR / relative_path, "r", encoding="utf-8") as f:
            logger.success(f"Файл {relative_path} загружен")
            return f.read()
    except FileNotFoundError:
        logger.error(f"Ошибка загрузки файла {relative_path}")
        return ""


# Загружаем файлы - теперь добавлять новые очень просто
styles_css = load_file("static/styles/styles.css")
# init
script_js = load_file("static/scripts/init/script.js")
# scriptsComponents
ranameBtn_js = load_file("static/scripts/scriptsComponents/renameBtn.js")
deleteBtn_js = load_file("static/scripts/scriptsComponents/deleteBtn.js")
simulateClickById_js = load_file("static/scripts/scriptsComponents/simulateClickById.js")
# global
fucusInput_js = load_file("static/scripts/global/focusInput.js")
customResizable_js = load_file("static/scripts/global/customResizable.js")
burgerMenu_js = load_file("static/scripts/global/burgerMenu.js")
# Добавить новый файл: new_file = load_file("path/to/new/file.js")