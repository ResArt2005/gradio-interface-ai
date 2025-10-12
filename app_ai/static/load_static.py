from pathlib import Path
BASE_DIR = Path(__file__).parent.parent

def load_file(relative_path: str) -> str:
    """Универсальная функция загрузки файлов"""
    try:
        with open(BASE_DIR / relative_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

# Загружаем файлы - теперь добавлять новые очень просто
styles_css = load_file("static/styles/styles.css")
script_js = load_file("static/scripts/script.js")
ranameBtn_js = load_file("static/scripts/renameBtn.js")
fucusInput_js = load_file("static/scripts/focusInput.js")
simulateClickById_js = load_file("static/scripts/simulateClickById.js")

# Добавить новый файл: new_file = load_file("path/to/new/file.js")