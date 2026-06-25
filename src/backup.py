"""
Модуль для сравнения исходной папки с резервной копией.
Выявляет отсутствующие, измененные и лишние файлы.
"""

import os
from datetime import datetime
from hasher import calculate_file_hash


def compare_with_backup(db, source_path, backup_path, algorithm='sha256', use_hashes=True):
    """
    Сравнивает исходную папку с резервной копией.

    Args:
        db: Объект Database с активным соединением
        source_path: Путь к исходной папке
        backup_path: Путь к резервной копии
        algorithm: Алгоритм хэширования для сравнения содержимого
        use_hashes: Использовать хэши для точного сравнения (True) или только размер/дату (False)

    Returns:
        Словарь с результатами сравнения
    """
    cursor = db.cursor

    print(f"Сравнение папок:")
    print(f"  Источник: {source_path}")
    print(f"  Бэкап:    {backup_path}")

    # 1. Сканируем обе папки
    print("\nСканирование исходной папки...")
    source_files = scan_folder_relative(source_path)
    print(f"  Найдено: {len(source_files)} файлов")

    print("Сканирование резервной копии...")
    backup_files = scan_folder_relative(backup_path)
    print(f"  Найдено: {len(backup_files)} файлов")

    # 2. Создаем словари для быстрого поиска
    source_dict = {f['relative_path']: f for f in source_files}
    backup_dict = {f['relative_path']: f for f in backup_files}

    # 3. Сравниваем
    results = {
        'missing': [],  # Есть в бэкапе, но нет в источнике
        'extra': [],  # Есть в источнике, но нет в бэкапе
        'changed': [],  # Есть в обоих, но отличаются
        'unchanged': [],  # Одинаковые
        'errors': []  # Ошибки при сравнении
    }

    # Проверяем все файлы из источника
    for path, source_info in source_dict.items():
        if path not in backup_dict:
            # Файл отсутствует в бэкапе
            results['extra'].append({
                'relative_path': path,
                'size_bytes': source_info['size_bytes'],
                'source_modified': source_info['modified_at'],
                'backup_modified': None
            })
        else:
            # Файл есть в обоих - сравниваем
            backup_info = backup_dict[path]

            # Быстрая проверка по размеру и дате
            if (source_info['size_bytes'] == backup_info['size_bytes'] and
                    source_info['modified_at'] == backup_info['modified_at']):

                if use_hashes:
                    # Точная проверка по хэшу
                    source_hash = calculate_file_hash(
                        os.path.join(source_path, path), algorithm
                    )
                    backup_hash = calculate_file_hash(
                        os.path.join(backup_path, path), algorithm
                    )

                    if source_hash and backup_hash and source_hash == backup_hash:
                        results['unchanged'].append({
                            'relative_path': path,
                            'size_bytes': source_info['size_bytes']
                        })
                    else:
                        results['changed'].append({
                            'relative_path': path,
                            'size_bytes_source': source_info['size_bytes'],
                            'size_bytes_backup': backup_info['size_bytes'],
                            'source_modified': source_info['modified_at'],
                            'backup_modified': backup_info['modified_at'],
                            'hash_different': True
                        })
                else:
                    results['unchanged'].append({
                        'relative_path': path,
                        'size_bytes': source_info['size_bytes']
                    })
            else:
                # Размер или дата отличаются
                change_info = {
                    'relative_path': path,
                    'size_bytes_source': source_info['size_bytes'],
                    'size_bytes_backup': backup_info['size_bytes'],
                    'source_modified': source_info['modified_at'],
                    'backup_modified': backup_info['modified_at'],
                    'hash_different': None  # Будет определено ниже
                }

                if use_hashes:
                    source_hash = calculate_file_hash(
                        os.path.join(source_path, path), algorithm
                    )
                    backup_hash = calculate_file_hash(
                        os.path.join(backup_path, path), algorithm
                    )

                    if source_hash and backup_hash:
                        change_info['hash_different'] = (source_hash != backup_hash)

                results['changed'].append(change_info)

    # Проверяем файлы, которые есть в бэкапе, но нет в источнике
    for path, backup_info in backup_dict.items():
        if path not in source_dict:
            results['missing'].append({
                'relative_path': path,
                'size_bytes': backup_info['size_bytes'],
                'backup_modified': backup_info['modified_at']
            })

    # 4. Сохраняем результаты в БД
    save_check_results(db, source_path, backup_path, results)

    return results


def scan_folder_relative(folder_path):
    """
    Сканирует папку и возвращает словарь с относительными путями.

    Args:
        folder_path: Путь к папке

    Returns:
        Список словарей с метаданными
    """
    files_data = []

    if not os.path.exists(folder_path):
        print(f"  ⚠ Папка не существует: {folder_path}")
        return files_data

    for root, dirs, files in os.walk(folder_path):
        # Пропускаем скрытые папки
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in files:
            if filename.startswith('.'):
                continue

            file_path = os.path.join(root, filename)

            try:
                stat_info = os.stat(file_path)
                relative_path = os.path.relpath(file_path, folder_path)

                files_data.append({
                    'relative_path': relative_path,
                    'file_name': filename,
                    'size_bytes': stat_info.st_size,
                    'modified_at': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

            except (PermissionError, OSError):
                continue

    return files_data


def save_check_results(db, source_path, backup_path, results):
    """
    Сохраняет результаты проверки в базу данных.

    Args:
        db: Объект Database
        source_path: Путь к исходной папке
        backup_path: Путь к бэкапу
        results: Результаты сравнения
    """
    cursor = db.cursor
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Создаем запись о проверке
    total_issues = len(results['missing']) + len(results['extra']) + len(results['changed'])

    summary = (
        f"Проверка: {source_path} <-> {backup_path}\n"
        f"Отсутствует в источнике: {len(results['missing'])}\n"
        f"Лишних в источнике: {len(results['extra'])}\n"
        f"Изменено: {len(results['changed'])}\n"
        f"Без изменений: {len(results['unchanged'])}\n"
        f"Ошибок: {len(results['errors'])}"
    )

    cursor.execute("""
        INSERT INTO check_results (check_type, backup_path, checked_at, result_summary)
        VALUES (?, ?, ?, ?)
    """, ('backup_comparison', backup_path, now, summary))

    check_id = cursor.lastrowid

    # Сохраняем детали по каждой категории

    # Отсутствующие файлы
    for item in results['missing']:
        cursor.execute("""
            INSERT INTO check_details (check_id, relative_path, status, details)
            VALUES (?, ?, 'missing', ?)
        """, (check_id, item['relative_path'],
              f"Отсутствует в источнике, есть в бэкапе ({item['size_bytes']} байт)"))

    # Лишние файлы
    for item in results['extra']:
        cursor.execute("""
            INSERT INTO check_details (check_id, relative_path, status, details)
            VALUES (?, ?, 'extra', ?)
        """, (check_id, item['relative_path'],
              f"Есть в источнике, отсутствует в бэкапе ({item['size_bytes']} байт)"))

    # Измененные файлы
    for item in results['changed']:
        details = (
            f"Размер: {item['size_bytes_source']} -> {item['size_bytes_back']} байт, "
            f"Изменен: {item['source_modified']} -> {item['backup_modified']}"
        )
        if item.get('hash_different') is not None:
            details += f", Хэш: {'различается' if item['hash_different'] else 'совпадает'}"

        cursor.execute("""
            INSERT INTO check_details (check_id, relative_path, status, details)
            VALUES (?, ?, 'changed', ?)
        """, (check_id, item['relative_path'], details))

    db.connection.commit()

    print(f"\n✓ Результаты сохранены в БД (проверка #{check_id})")

    return check_id


def get_check_history(db, limit=10):
    """
    Получает историю проверок.

    Args:
        db: Объект Database
        limit: Максимальное количество записей

    Returns:
        Список записей о проверках
    """
    cursor = db.cursor

    cursor.execute("""
        SELECT id, check_type, backup_path, checked_at, result_summary
        FROM check_results
        ORDER BY checked_at DESC
        LIMIT ?
    """, (limit,))

    columns = ['id', 'check_type', 'backup_path', 'checked_at', 'result_summary']
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_check_details(db, check_id):
    """
    Получает детали конкретной проверки.

    Args:
        db: Объект Database
        check_id: ID проверки

    Returns:
        Список деталей проверки
    """
    cursor = db.cursor

    cursor.execute("""
        SELECT relative_path, status, details
        FROM check_details
        WHERE check_id = ?
        ORDER BY status, relative_path
    """, (check_id,))

    columns = ['relative_path', 'status', 'details']
    return [dict(zip(columns, row)) for row in cursor.fetchall()]