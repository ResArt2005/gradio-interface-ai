from tools.DBPostgresqlGradio import db
'''from pathlib import Path
import json
def parse_hierarchy(lines:list[str])->list[dict[str, any]]:
    """
    Парсит список строк в иерархическую структуру списка словарей.
    Уровень определяется количеством дефисов '-' в начале строки.
    """
    root = []
    stack = [(0, root)]  # (уровень, список для добавления)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue  # пропускаем пустые строки

        # Определяем уровень по количеству дефисов в начале
        level = 0
        while stripped.startswith('-'):
            level += 1
            stripped = stripped[1:].strip()

        node = {"name": stripped, "children": []}

        # Поднимаемся по стеку, пока не найдём подходящий уровень
        while stack and stack[-1][0] >= level + 1:
            stack.pop()

        # Добавляем текущий узел в список на нужном уровне
        stack[-1][1].append(node)
        stack.append((level + 1, node["children"]))

    return root

tree:dict[str, any]
#if __name__ == "__main__":
file_path = Path(__file__).parent / "fast_prompt_list.txt"
print(f"Чтение файла: {file_path}")
try:
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()
    # Парсим иерархию из строк
    tree = parse_hierarchy(lines)

    # Красиво выводим в JSON для проверки
    print(json.dumps(tree, ensure_ascii=False, indent=4))
except FileNotFoundError:
    print("⚠️  Файл с быстрыми запросами не найден")
'''
#print(db.get_tree_as_json())
tree = db.get_tree_as_json()