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

    # Получаем список всех файлов, которые сейчас есть в БД
    cursor.execute("SELECT id, relative_path FROM files WHERE is_present = 1")
    existing_files = {row[1]: row[0] for row in cursor.fetchall()}

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

        if relative_path in existing_files:
            # Файл уже есть в БД - проверяем, изменился ли
            file_id = existing_files[relative_path]

            cursor.execute("""
                SELECT size_bytes, modified_at 
                FROM files 
                WHERE id = ?
            """, (file_id,))

            old_data = cursor.fetchone()

            # Сравниваем размер и дату модификации
            if (old_data[0] != file_data['size_bytes'] or
                    old_data[1] != file_data['modified_at']):

                cursor.execute("""
                    UPDATE files 
                    SET size_bytes = ?, modified_at = ?, is_present = 1
                    WHERE id = ?
                """, (file_data['size_bytes'], file_data['modified_at'], file_id))
                stats['updated'] += 1
            else:
                # Обновляем is_present на всякий случай
                cursor.execute("UPDATE files SET is_present = 1 WHERE id = ?", (file_id,))
                stats['unchanged'] += 1
        else:
            # Новый файл - добавляем
            cursor.execute("""
                INSERT INTO files (relative_path, file_name, extension, size_bytes, modified_at, file_type, is_present)
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
    for path, file_id in existing_files.items():
        if path not in scanned_paths:
            cursor.execute("UPDATE files SET is_present = 0 WHERE id = ?", (file_id,))
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
        cursor.execute("SELECT * FROM files WHERE is_present = 1 ORDER BY relative_path")
    else:
        cursor.execute("SELECT * FROM files ORDER BY relative_path")

    columns = ['id', 'relative_path', 'file_name', 'extension',
               'size_bytes', 'modified_at', 'file_type', 'is_present']

    return [dict(zip(columns, row)) for row in cursor.fetchall()]