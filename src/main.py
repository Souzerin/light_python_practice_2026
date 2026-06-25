"""
Console File Indexer
Точка входа в приложение.
Полный функционал: сканирование, дубликаты, сравнение с бэкапом.
"""

import sys
import os
from database import Database
from scanner import scan_folder
from indexer import update_index, get_indexed_files
from hasher import calculate_hashes_for_files
from duplicates import find_duplicates, find_duplicates_by_size
from backup import compare_with_backup, get_check_history, get_check_details
from reporter import (
    print_scan_report,
    print_index_stats,
    print_hash_stats,
    print_duplicate_report,
    print_backup_report,
    print_check_history
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
        (command, params) - команда и параметры
    """
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = 'scan'  # По умолчанию
    params = {
        'folder_path': None,
        'backup_path': None,
        'filters': [],
        'show_history': False
    }

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg in ('--help', '-h'):
            print_help()
            sys.exit(0)

        elif arg in ('--scan', '--index'):
            command = 'scan'

        elif arg in ('--duplicates', '--find-duplicates', '--dups'):
            command = 'duplicates'

        elif arg in ('--backup', '--compare'):
            command = 'backup'
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                params['backup_path'] = sys.argv[i + 1]
                i += 1

        elif arg == '--history':
            params['show_history'] = True

        elif arg == '--ext' and i + 1 < len(sys.argv):
            extensions = []
            i += 1
            while i < len(sys.argv) and sys.argv[i].startswith('.'):
                extensions.append(sys.argv[i])
                i += 1
            params['filters'].append(filter_by_extension(extensions))
            continue

        elif arg == '--name' and i + 1 < len(sys.argv):
            pattern = sys.argv[i + 1]
            params['filters'].append(filter_by_name_pattern(pattern))
            i += 2
            continue

        elif arg == '--min-size' and i + 1 < len(sys.argv):
            size = int(sys.argv[i + 1])
            params['filters'].append(filter_by_min_size(size))
            i += 2
            continue

        elif arg == '--max-size' and i + 1 < len(sys.argv):
            size = int(sys.argv[i + 1])
            params['filters'].append(filter_by_max_size(size))
            i += 2
            continue

        elif arg == '--text-only':
            params['filters'].append(filter_text_only)

        elif arg == '--media-only':
            params['filters'].append(filter_media_only)

        elif arg == '--py-only':
            params['filters'].append(filter_python_only)

        elif arg == '--all':
            params['filters'] = []

        elif not arg.startswith('--') and params['folder_path'] is None:
            params['folder_path'] = arg
        elif not arg.startswith('--') and params['folder_path'] is not None and params['backup_path'] is None:
            params['backup_path'] = arg

        i += 1

    return command, params


def print_help():
    """Выводит справку."""
    print("=" * 70)
    print("КОНСОЛЬНЫЙ ИНДЕКСАТОР ФАЙЛОВ")
    print("=" * 70)
    print("\nИспользование:")
    print("  py src/main.py <путь> [команда] [опции]")
    print("\nКоманды:")
    print("  --scan (по умолчанию)  - сканирование и индексация")
    print("  --dups                 - поиск дубликатов")
    print("  --backup <путь>        - сравнение с резервной копией")
    print("  --history              - показать историю проверок")
    print("\nОпции фильтрации:")
    print("  --ext .py .txt     - только указанные расширения")
    print("  --name pattern      - фильтр по имени")
    print("  --min-size BYTES    - минимальный размер")
    print("  --max-size BYTES    - максимальный размер")
    print("  --text-only         - только текстовые")
    print("  --media-only        - только медиа")
    print("  --py-only           - только Python")
    print("  --all               - все файлы (без фильтра)")
    print("\nПримеры:")
    print("  py src/main.py E:\\project --scan --all")
    print("  py src/main.py E:\\project --dups")
    print("  py src/main.py E:\\project --backup E:\\backup")
    print("  py src/main.py E:\\project --backup E:\\backup --history")
    print("  py src/main.py E:\\project --scan --ext .py .txt")
    print("  py src/main.py --help")


def main():
    """Главная функция."""

    command, params = parse_args()

    print("=" * 70)
    print("КОНСОЛЬНЫЙ ИНДЕКСАТОР ФАЙЛОВ")
    print("=" * 70)

    # Инициализация БД
    db_path = os.path.join("data", "app.db")
    db = Database(db_path)

    try:
        db.initialize()

        if params['show_history']:
            # Показываем историю проверок
            history = get_check_history(db)
            print_check_history(history)
            return

        # Проверяем, что указан путь к папке
        if not params['folder_path']:
            print("\n❌ ОШИБКА: Не указан путь к папке!")
            print("Использование: py src/main.py <путь> [команда]")
            return

        folder_path = os.path.abspath(params['folder_path'])

        if not os.path.exists(folder_path):
            print(f"\n❌ ОШИБКА: Папка '{folder_path}' не существует!")
            return

        if not os.path.isdir(folder_path):
            print(f"❌ ОШИБКА: '{folder_path}' не является папкой!")
            return

        print(f"✓ Папка: {folder_path}")
        print(f"✓ Команда: {command}")

        if command == 'scan':
            run_scan(db, folder_path, params['filters'])

        elif command == 'duplicates':
            run_duplicates(db, folder_path)

        elif command == 'backup':
            if not params['backup_path']:
                print("\n❌ ОШИБКА: Не указан путь к резервной копии!")
                print("Использование: py src/main.py <путь> --backup <путь_к_бэкапу>")
                return

            backup_path = os.path.abspath(params['backup_path'])
            run_backup(db, folder_path, backup_path)

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
    """Сканирование и индексация."""
    if filters:
        print(f"✓ Фильтры: активно {len(filters)} фильтр(ов)")
    else:
        print("✓ Фильтры: отключены (показаны все файлы)")

    print("\n--- СКАНИРОВАНИЕ ---")
    scanned_files = scan_folder(folder_path, filters=filters if filters else None)
    print_scan_report(scanned_files)

    print("\n--- ОБНОВЛЕНИЕ ИНДЕКСА ---")
    stats = update_index(db, scanned_files, folder_path)
    print_index_stats(stats)

    indexed = get_indexed_files(db)
    print(f"\n✓ Всего файлов в индексе: {len(indexed)}")

    print("\n--- ДАННЫЕ В БД (первые 10 записей) ---")
    for f in indexed[:10]:
        print(f"  {f['relative_path']:45} {f['size_bytes']:>8} байт | {f['file_type']:10} | {f['modified_at']}")


def run_duplicates(db, folder_path):
    """Поиск дубликатов."""
    algorithm = 'sha256'
    print(f"✓ Алгоритм: {algorithm}")

    print("\n--- ПОЛУЧЕНИЕ ИНДЕКСА ---")
    indexed_files = get_indexed_files(db, only_present=True)
    print(f"✓ Файлов в индексе: {len(indexed_files)}")

    if not indexed_files:
        print("❌ Нет файлов в индексе. Сначала выполните: py src/main.py <путь> --scan")
        return

    print("\n--- ПРЕДВАРИТЕЛЬНЫЙ АНАЛИЗ ПО РАЗМЕРУ ---")
    size_groups = find_duplicates_by_size(db, min_group_size=2)
    if size_groups:
        print(f"Найдено {len(size_groups)} групп с одинаковым размером:")
        for i, group in enumerate(size_groups[:5], 1):
            print(f"  {i}. Размер: {format_size(group['size_bytes']):>10} | "
                  f"Файлов: {group['file_count']}")

    print(f"\n--- ВЫЧИСЛЕНИЕ ХЭШЕЙ ---")
    hash_stats = calculate_hashes_for_files(db, folder_path, indexed_files, algorithm)
    print_hash_stats(hash_stats)

    print(f"\n--- ПОИСК ДУБЛИКАТОВ ---")
    duplicate_groups = find_duplicates(db, algorithm, min_group_size=2)
    print_duplicate_report(duplicate_groups)


def run_backup(db, source_path, backup_path):
    """Сравнение с резервной копией."""
    print(f"✓ Исходная папка: {source_path}")
    print(f"✓ Резервная копия: {backup_path}")

    if not os.path.exists(backup_path):
        print(f"\n❌ ОШИБКА: Папка бэкапа '{backup_path}' не существует!")
        return

    print("\n--- СРАВНЕНИЕ ПАПОК ---")
    results = compare_with_backup(db, source_path, backup_path, use_hashes=True)
    print_backup_report(results)

    # Показываем историю проверок
    print("\n--- ИСТОРИЯ ПРОВЕРОК ---")
    history = get_check_history(db, limit=5)
    print_check_history(history)


def format_size(size_bytes):
    """Форматирует размер."""
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    main()