import sys
import os
from database import Database


def main():
    """Главная функция приложения."""
    if len(sys.argv) < 2:
        print("Ошибка: Не указан путь к папке.")
        print("Использование: python main.py <путь_к_папке>")
        sys.exit(1)

    folder_path = sys.argv[1]

    # Проверка существования папки
    if not os.path.exists(folder_path):
        print(f"Ошибка: Папка '{folder_path}' не существует.")
        sys.exit(1)

    if not os.path.isdir(folder_path):
        print(f"Ошибка: '{folder_path}' не является папкой.")
        sys.exit(1)

    # Преобразование в абсолютный путь
    folder_path = os.path.abspath(folder_path)
    print(f"Индексация папки: {folder_path}")

    # Инициализация базы данных
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "app.db")
    db = Database(db_path)

    try:
        db.initialize()
        print(f"База данных создана: {db_path}")
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
        sys.exit(1)
    finally:
        db.close()