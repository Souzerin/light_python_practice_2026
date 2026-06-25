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
from filters import (
    filter_by_extension,
    filter_by_name_pattern,
    filter_by_min_size,
    filter_by_max_size,
    filter_text_only,
    filter_media_only,
    filter_python_only
)


def parse_args():
    """
    Разбирает аргументы командной строки.

    Возвращает:
        (folder_path, filters) - путь к папке и список фильтров
    """
    if len(sys.argv) < 2:
        print("=" * 70)
        print("КОНСОЛЬНЫЙ ИНДЕКСАТОР ФАЙЛОВ")
        print("=" * 70)
        print("\nИспользование:")
        print("  py src/main.py <путь_к_папке> [опции]")
        print("\nОпции фильтрации:")
        print("  --ext .py .txt     - только указанные расширения")
        print("  --name pattern      - фильтр по имени (содержит подстроку)")
        print("  --min-size BYTES    - минимальный размер в байтах")
        print("  --max-size BYTES    - максимальный размер в байтах")
        print("  --text-only         - только текстовые файлы")
        print("  --media-only        - только медиафайлы (изображения, аудио, видео)")
        print("  --py-only           - только Python файлы")
        print("  --all               - все файлы (без фильтра)")
        print("\nПримеры:")
        print("  py src/main.py E:\\project --ext .py .txt")
        print("  py src/main.py E:\\project --text-only")
        print("  py src/main.py E:\\project --all")
        print("  py src/main.py E:\\project --ext .py --min-size 1000")
        sys.exit(0)

    folder_path = sys.argv[1]
    filters = []

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--ext' and i + 1 < len(sys.argv):
            extensions = []
            i += 1
            while i < len(sys.argv) and sys.argv[i].startswith('.'):
                extensions.append(sys.argv[i])
                i += 1
            filters.append(filter_by_extension(extensions))
            continue

        elif arg == '--name' and i + 1 < len(sys.argv):
            pattern = sys.argv[i + 1]
            filters.append(filter_by_name_pattern(pattern))
            i += 2
            continue

        elif arg == '--min-size' and i + 1 < len(sys.argv):
            size = int(sys.argv[i + 1])
            filters.append(filter_by_min_size(size))
            i += 2
            continue

        elif arg == '--max-size' and i + 1 < len(sys.argv):
            size = int(sys.argv[i + 1])
            filters.append(filter_by_max_size(size))
            i += 2
            continue

        elif arg == '--text-only':
            filters.append(filter_text_only)

        elif arg == '--media-only':
            filters.append(filter_media_only)

        elif arg == '--py-only':
            filters.append(filter_python_only)

        elif arg == '--all':
            filters = []  # Без фильтров
            break

        i += 1

    return folder_path, filters


def main():
    """Главная функция приложения."""

    # Разбор аргументов
    folder_path, filters = parse_args()

    print("=" * 70)
    print("КОНСОЛЬНЫЙ ИНДЕКСАТОР ФАЙЛОВ")
    print("=" * 70)

    # Проверка существования папки
    if not os.path.exists(folder_path):
        print(f"❌ ОШИБКА: Папка '{folder_path}' не существует!")
        return

    if not os.path.isdir(folder_path):
        print(f"❌ ОШИБКА: '{folder_path}' не является папкой!")
        return

    folder_path = os.path.abspath(folder_path)
    print(f"✓ Папка: {folder_path}")

    # Вывод активных фильтров
    if filters:
        print(f"✓ Фильтры: активно {len(filters)} фильтр(ов)")
    else:
        print("✓ Фильтры: отключены (показаны все файлы)")

    # Инициализация БД
    db_path = os.path.join("data", "app.db")
    print(f"✓ База данных: {db_path}")

    db = Database(db_path)

    try:
        # Инициализируем БД
        db.initialize()

        # 1. Сканируем папку
        print("\n--- СКАНИРОВАНИЕ ---")
        scanned_files = scan_folder(folder_path, filters=filters if filters else None)

        # 2. Выводим отчет о сканировании
        print_scan_report(scanned_files)

        # 3. Обновляем индекс в БД
        print("\n--- ОБНОВЛЕНИЕ ИНДЕКСА ---")
        stats = update_index(db, scanned_files, folder_path)
        print_index_stats(stats)

        # 4. Проверяем что в БД
        indexed = get_indexed_files(db)
        print(f"\n✓ Всего файлов в индексе: {len(indexed)}")

        # 5. Вывод примеров данных из БД (проверяемость)
        print("\n--- ДАННЫЕ В БД (первые 10 записей) ---")
        for f in indexed[:10]:
            print(f"  {f['relative_path']:45} {f['size_bytes']:>8} байт | {f['file_type']:10} | {f['modified_at']}")

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