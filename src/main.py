"""
Console File Indexer
Точка входа в приложение.
"""

import sys
import os
from database import Database
from scanner import scan_folder
from indexer import update_index, get_indexed_files
from hasher import calculate_hashes_for_files
from duplicates import find_duplicates, find_duplicates_by_size
from reporter import (
    print_scan_report,
    print_index_stats,
    print_hash_stats,
    print_duplicate_report
)
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
        (folder_path, filters, command) - путь, фильтры, команда
    """
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    folder_path = sys.argv[1]
    filters = []
    command = 'scan'  # По умолчанию - сканирование

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg in ('--duplicates', '--find-duplicates'):
            command = 'duplicates'

        elif arg in ('--scan', '--index'):
            command = 'scan'

        elif arg == '--ext' and i + 1 < len(sys.argv):
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
            filters = []
            break

        elif arg in ('--algorithm', '--algo') and i + 1 < len(sys.argv):
            # Можно указать алгоритм хэширования
            pass  # Пока используем sha256 по умолчанию

        i += 1

    return folder_path, filters, command


def print_help():
    """Выводит справку по использованию."""
    print("=" * 70)
    print("КОНСОЛЬНЫЙ ИНДЕКСАТОР ФАЙЛОВ")
    print("=" * 70)
    print("\nИспользование:")
    print("  py src/main.py <путь_к_папке> [команда] [опции]")
    print("\nКоманды:")
    print("  --scan (по умолчанию)  - сканирование и индексация")
    print("  --duplicates           - поиск дубликатов")
    print("\nОпции фильтрации (для --scan):")
    print("  --ext .py .txt     - только указанные расширения")
    print("  --name pattern      - фильтр по имени")
    print("  --min-size BYTES    - минимальный размер")
    print("  --max-size BYTES    - максимальный размер")
    print("  --text-only         - только текстовые")
    print("  --media-only        - только медиа")
    print("  --py-only           - только Python")
    print("  --all               - все файлы")
    print("\nПримеры:")
    print("  py src/main.py E:\\project --scan --all")
    print("  py src/main.py E:\\project --duplicates")
    print("  py src/main.py E:\\project --scan --ext .py .txt")
    print("  py src/main.py . --duplicates")


def main():
    """Главная функция приложения."""

    folder_path, filters, command = parse_args()

    print("=" * 70)
    print("КОНСОЛЬНЫЙ ИНДЕКСАТОР ФАЙЛОВ")
    print("=" * 70)

    # Проверка папки
    if not os.path.exists(folder_path):
        print(f"❌ ОШИБКА: Папка '{folder_path}' не существует!")
        return

    if not os.path.isdir(folder_path):
        print(f"❌ ОШИБКА: '{folder_path}' не является папкой!")
        return

    folder_path = os.path.abspath(folder_path)
    print(f"✓ Папка: {folder_path}")
    print(f"✓ Команда: {command}")

    # Инициализация БД
    db_path = os.path.join("data", "app.db")
    db = Database(db_path)

    try:
        db.initialize()

        if command == 'scan':
            run_scan(db, folder_path, filters)
        elif command == 'duplicates':
            run_duplicates(db, folder_path)

        print("\n" + "=" * 70)
        print("ГОТОВО!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def run_scan(db, folder_path, filters):
    """Выполняет сканирование и индексацию."""

    if filters:
        print(f"✓ Фильтры: активно {len(filters)} фильтр(ов)")
    else:
        print("✓ Фильтры: отключены (показаны все файлы)")

    print(f"✓ База данных: {db.db_path}")

    # Сканирование
    print("\n--- СКАНИРОВАНИЕ ---")
    scanned_files = scan_folder(folder_path, filters=filters if filters else None)

    # Отчет
    print_scan_report(scanned_files)

    # Обновление индекса
    print("\n--- ОБНОВЛЕНИЕ ИНДЕКСА ---")
    stats = update_index(db, scanned_files, folder_path)
    print_index_stats(stats)

    # Проверка
    indexed = get_indexed_files(db)
    print(f"\n✓ Всего файлов в индексе: {len(indexed)}")

    # Вывод данных из БД
    print("\n--- ДАННЫЕ В БД (первые 10 записей) ---")
    for f in indexed[:10]:
        print(f"  {f['relative_path']:45} {f['size_bytes']:>8} байт | {f['file_type']:10} | {f['modified_at']}")


def run_duplicates(db, folder_path):
    """Выполняет поиск дубликатов."""

    algorithm = 'sha256'

    print(f"✓ Алгоритм: {algorithm}")
    print(f"✓ База данных: {db.db_path}")

    # Получаем список проиндексированных файлов
    print("\n--- ПОЛУЧЕНИЕ ИНДЕКСА ---")
    indexed_files = get_indexed_files(db, only_present=True)
    print(f"✓ Файлов в индексе: {len(indexed_files)}")

    if not indexed_files:
        print("❌ Нет файлов в индексе. Сначала выполните сканирование:")
        print("   py src/main.py <путь> --scan --all")
        return

    # Быстрый предварительный анализ по размеру
    print("\n--- ПРЕДВАРИТЕЛЬНЫЙ АНАЛИЗ ПО РАЗМЕРУ ---")
    size_groups = find_duplicates_by_size(db, min_group_size=2)
    if size_groups:
        print(f"Найдено {len(size_groups)} групп файлов с одинаковым размером")
        print("Топ-5 групп для проверки хэшами:")
        for i, group in enumerate(size_groups[:5], 1):
            print(f"  {i}. Размер: {format_size(group['size_bytes']):>10} | "
                  f"Файлов: {group['file_count']}")

    # Вычисление хэшей
    print(f"\n--- ВЫЧИСЛЕНИЕ ХЭШЕЙ ---")
    hash_stats = calculate_hashes_for_files(db, folder_path, indexed_files, algorithm)
    print_hash_stats(hash_stats)

    # Поиск дубликатов
    print(f"\n--- ПОИСК ДУБЛИКАТОВ ---")
    duplicate_groups = find_duplicates(db, algorithm, min_group_size=2)

    # Вывод отчета
    print_duplicate_report(duplicate_groups)


def format_size(size_bytes):
    """Форматирует размер (дублируется в main для удобства)."""
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    main()