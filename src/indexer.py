"""
Модуль для индексации файлов в базе данных.
Синхронизирует результаты сканирования с SQLite.
"""

from datetime import datetime


def update_index(db, scanned_files, folder_path):
    """
    Обновляет индекс файлов в БД на основе результатов сканирования.

    Логика:
    - Новые файлы добавляются
    - Существующие файлы обновляются
    - Файлы, которых нет в сканировании, помечаются как отсутствующие

    Args:
        db: Объект Database с активным соединением
        scanned_files: Список словарей с метаданными файлов
        folder_path: Путь к сканируемой папке (для записи в историю)

    Returns:
        Словарь со статистикой изменений
    """
    cursor = db.cursor

    # Получаем список ВСЕХ файлов, которые есть в БД (включая отсутствующие)
    cursor.execute("SELECT id, relative_path, size_bytes, modified_at FROM files")
    all_db_files = {}
    for row in cursor.fetchall():
        all_db_files[row[1]] = {
            'id': row[0],
            'size_bytes': row[2],
            'modified_at': row[3]
        }

    # Множество путей из нового сканирования
    scanned_paths = set()

    stats = {
        'added': 0,
        'updated': 0,
        'removed': 0,
        'unchanged': 0
    }

    for file_data in scanned_files:
        relative_path = file_data['relative_path']
        scanned_paths.add(relative_path)

        if relative_path in all_db_files:
            # Файл уже есть в БД - проверяем, изменился ли
            existing = all_db_files[relative_path]
            file_id = existing['id']

            # Сравниваем размер и дату модификации
            if (existing['size_bytes'] != file_data['size_bytes'] or
                    existing['modified_at'] != file_data['modified_at']):

                # Данные изменились - обновляем запись
                cursor.execute("""
                    UPDATE files 
                    SET size_bytes = ?, 
                        modified_at = ?, 
                        is_present = 1,
                        file_name = ?,
                        extension = ?,
                        file_type = ?
                    WHERE id = ?
                """, (
                    file_data['size_bytes'],
                    file_data['modified_at'],
                    file_data['file_name'],
                    file_data['extension'],
                    file_data['file_type'],
                    file_id
                ))
                stats['updated'] += 1
            else:
                # Данные не изменились - просто помечаем как присутствующий
                cursor.execute("""
                    UPDATE files 
                    SET is_present = 1 
                    WHERE id = ?
                """, (file_id,))
                stats['unchanged'] += 1
        else:
            # Новый файл - добавляем
            cursor.execute("""
                INSERT INTO files 
                (relative_path, file_name, extension, size_bytes, modified_at, file_type, is_present)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                file_data['relative_path'],
                file_data['file_name'],
                file_data['extension'],
                file_data['size_bytes'],
                file_data['modified_at'],
                file_data['file_type']
            ))
            stats['added'] += 1

    # Помечаем отсутствующие файлы
    # Те файлы что есть в БД, но не найдены при текущем сканировании
    for path, info in all_db_files.items():
        if path not in scanned_paths:
            cursor.execute("""
                UPDATE files 
                SET is_present = 0 
                WHERE id = ?
            """, (info['id'],))
            stats['removed'] += 1

    # Сохраняем изменения
    db.connection.commit()

    return stats


def get_indexed_files(db, only_present=True):
    """
    Получает список файлов из индекса.

    Args:
        db: Объект Database
        only_present: Если True, возвращает только присутствующие файлы

    Returns:
        Список словарей с метаданными
    """
    cursor = db.cursor

    if only_present:
        cursor.execute("""
            SELECT id, relative_path, file_name, extension, 
                   size_bytes, modified_at, file_type, is_present
            FROM files 
            WHERE is_present = 1 
            ORDER BY relative_path
        """)
    else:
        cursor.execute("""
            SELECT id, relative_path, file_name, extension, 
                   size_bytes, modified_at, file_type, is_present
            FROM files 
            ORDER BY relative_path
        """)

    columns = ['id', 'relative_path', 'file_name', 'extension',
               'size_bytes', 'modified_at', 'file_type', 'is_present']

    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def reset_index(db):
    """
    Полностью очищает индекс файлов.
    Полезно если нужно начать с чистого листа.

    Args:
        db: Объект Database
    """
    cursor = db.cursor
    cursor.execute("DELETE FROM files")
    cursor.execute("DELETE FROM file_hashes")
    db.connection.commit()
    print("✓ Индекс полностью очищен")