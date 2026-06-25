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


def print_hash_stats(stats):
    """
    Выводит статистику вычисления хэшей.

    Args:
        stats: Словарь со статистикой хэширования
    """
    print("\n" + "-" * 40)
    print("Результаты хэширования:")
    print(f"  Всего файлов:        {stats['total']:5}")
    print(f"  Посчитано сейчас:    {stats['calculated']:5}")
    print(f"  Взято из кэша:       {stats['from_cache']:5}")
    print(f"  Ошибок:              {stats['errors']:5}")
    print("-" * 40)


def print_duplicate_report(duplicate_groups, max_groups_display=20, max_files_in_group=10):
    """
    Выводит отчет о найденных дубликатах.

    Args:
        duplicate_groups: Список групп дубликатов
        max_groups_display: Максимальное количество групп для вывода
        max_files_in_group: Максимальное количество файлов в группе для вывода
    """
    if not duplicate_groups:
        print("\n" + "=" * 70)
        print("✓ ДУБЛИКАТЫ НЕ НАЙДЕНЫ")
        print("=" * 70)
        return

    print("\n" + "=" * 70)
    print(f"НАЙДЕНО ДУБЛИКАТОВ: {len(duplicate_groups)} групп")
    print("=" * 70)

    # Статистика
    stats = get_duplicate_stats(duplicate_groups)

    print(f"\nОбщая статистика:")
    print(f"  Групп дубликатов:    {stats['total_groups']}")
    print(f"  Всего файлов-дублей: {stats['total_duplicate_files']}")
    print(f"  Потенциально можно освободить: {format_size(stats['wasted_space_bytes'])}")

    if stats['group_sizes']:
        print(f"\nРаспределение по размерам групп:")
        for size in sorted(stats['group_sizes'].keys()):
            print(f"  {size} файлов в группе: {stats['group_sizes'][size]} групп(ы)")

    # Вывод групп
    print(f"\n{'=' * 70}")
    print(f"ГРУППЫ ДУБЛИКАТОВ")
    print(f"{'=' * 70}")

    for i, group in enumerate(duplicate_groups[:max_groups_display], 1):
        print(f"\nГруппа #{i}: {group['file_count']} одинаковых файлов")
        print(f"  Хэш: {group['hash'][:32]}...")
        print(f"  Размер каждого файла: {format_size(group['total_size'] // group['file_count'])}")
        print(f"  Общий размер группы: {format_size(group['total_size'])}")
        print(f"  Можно освободить: {format_size(group['total_size'] - group['total_size'] // group['file_count'])}")
        print(f"\n  Файлы в группе:")

        for j, file_info in enumerate(group['files'][:max_files_in_group], 1):
            print(f"  {j:2}. {file_info['relative_path']}")
            print(f"      Размер: {format_size(file_info['size_bytes']):>10} | "
                  f"Изменен: {file_info['modified_at']}")

        if len(group['files']) > max_files_in_group:
            print(f"  ... и еще {len(group['files']) - max_files_in_group} файлов")

    if len(duplicate_groups) > max_groups_display:
        print(f"\n... и еще {len(duplicate_groups) - max_groups_display} групп")


def format_size(size_bytes):
    """
    Форматирует размер в байтах в читаемый вид.

    Args:
        size_bytes: Размер в байтах

    Returns:
        Строка с форматированным размером
    """
    if size_bytes == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"