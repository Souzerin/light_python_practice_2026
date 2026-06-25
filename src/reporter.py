"""
Модуль для форматирования и вывода отчетов в консоль.
"""


def print_scan_report(files, max_display=50):
    """
    Выводит отчет о просканированных файлах.

    Args:
        files: Список словарей с метаданными
        max_display: Максимальное количество файлов для вывода
    """
    if not files:
        print("\n" + "=" * 70)
        print("Файлы не найдены")
        print("=" * 70)
        return

    print("\n" + "=" * 70)
    print(f"Найдено файлов: {len(files)}")
    print("=" * 70)

    # Группировка по типам
    type_stats = {}
    total_size = 0

    for f in files:
        ftype = f.get('file_type', 'other')
        type_stats[ftype] = type_stats.get(ftype, 0) + 1
        total_size += f.get('size_bytes', 0)

    print("\nСтатистика по типам файлов:")
    for ftype, count in sorted(type_stats.items()):
        print(f"  {ftype:12} : {count:5}")

    print(f"\nОбщий размер: {format_size(total_size)}")

    # Вывод таблицы файлов
    print("\n" + "-" * 70)
    print(f"{'Относительный путь':45} {'Размер':>10} {'Изменен'}")
    print("-" * 70)

    for f in files[:max_display]:
        print(f"{f['relative_path']:45} {format_size(f['size_bytes']):>10} {f['modified_at']}")

    if len(files) > max_display:
        print(f"... и еще {len(files) - max_display} файлов")


def print_index_stats(stats):
    """
    Выводит статистику обновления индекса.

    Args:
        stats: Словарь со статистикой изменений
    """
    print("\n" + "-" * 40)
    print("Обновление индекса:")
    print(f"  + Добавлено:     {stats['added']:5}")
    print(f"  ~ Обновлено:     {stats['updated']:5}")
    print(f"  - Удалено:       {stats['removed']:5}")
    print(f"  = Без изменений: {stats['unchanged']:5}")
    print("-" * 40)


def format_size(size_bytes):
    """
    Форматирует размер в байтах в читаемый вид.

    Args:
        size_bytes: Размер в байтах

    Returns:
        Строка с форматированным размером
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"