"""
Console File Indexer
Точка входа в приложение.
"""

import sys
import os
from database import Database
from scanner import scan_folder
from indexer import update_index, get_indexed_files
from reporter import print_scan_report, print_index_stats
from filters import filter_by_extension


def main():
    """Главная функция приложения."""

    # Тестовый путь - замени на свою папку
    folder_path = r"E:\test_folder"  # ← ЗАМЕНИ НА СВОЮ ПАПКУ

    print("=" * 70)
    print("КОНСОЛЬНЫЙ ИНДЕКСАТОР ФАЙЛОВ")
    print("=" * 70)

    # Проверка существования папки
    if not os.path.exists(folder_path):
        print(f"❌ ОШИБКА: Папка '{folder_path}' не существует!")
        print("Создай папку или укажи правильный путь")
        return

    if not os.path.isdir(folder_path):
        print(f"❌ ОШИБКА: '{folder_path}' не является папкой!")
        return

    folder_path = os.path.abspath(folder_path)
    print(f"✓ Папка: {folder_path}")

    # Создаем фильтры (пример - только Python и текстовые файлы)
    filters = [
        filter_by_extension(['.py', '.txt', '.md', '.csv', '.json', '.log'])
    ]

    # Инициализация БД
    db_path = os.path.join("data", "app.db")
    print(f"✓ База данных: {db_path}")

    db = Database(db_path)

    try:
        # Инициализируем БД
        db.initialize()

        # 1. Сканируем папку
        print("\n--- СКАНИРОВАНИЕ ---")
        scanned_files = scan_folder(folder_path, filters=filters)

        # 2. Выводим отчет о сканировании
        print_scan_report(scanned_files)

        # 3. Обновляем индекс в БД
        print("\n--- ОБНОВЛЕНИЕ ИНДЕКСА ---")
        stats = update_index(db, scanned_files, folder_path)
        print_index_stats(stats)

        # 4. Проверяем что в БД
        indexed = get_indexed_files(db)
        print(f"\n✓ Всего в индексе: {len(indexed)} файлов")

        print("\n" + "=" * 70)
        print("ГОТОВО!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    main()