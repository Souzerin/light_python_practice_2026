"""
Модуль для вычисления хэшей содержимого файлов.
Поддерживает SHA256 (по умолчанию) и MD5.
"""

import hashlib
from datetime import datetime


def calculate_file_hash(file_path, algorithm='sha256', chunk_size=65536):
    """
    Вычисляет хэш содержимого файла.

    Args:
        file_path: Абсолютный путь к файлу
        algorithm: Алгоритм хэширования ('sha256', 'md5')
        chunk_size: Размер блока чтения в байтах

    Returns:
        Строка с хэшем в шестнадцатеричном формате или None при ошибке
    """
    try:
        hasher = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)

        return hasher.hexdigest()

    except (PermissionError, OSError) as e:
        print(f"  ⚠ Не удалось прочитать файл: {file_path}")
        print(f"    Ошибка: {e}")
        return None

    except ValueError as e:
        print(f"  ⚠ Неподдерживаемый алгоритм: {algorithm}")
        return None


def calculate_hashes_for_files(db, folder_path, indexed_files, algorithm='sha256', force_recalculate=False):
    """
    Вычисляет хэши для списка файлов и сохраняет в БД.

    Args:
        db: Объект Database с активным соединением
        folder_path: Абсолютный путь к сканируемой папке
        indexed_files: Список словарей с метаданными (из get_indexed_files)
        algorithm: Алгоритм хэширования
        force_recalculate: Если True, пересчитывает даже существующие хэши

    Returns:
        Словарь со статистикой
    """
    cursor = db.cursor
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    stats = {
        'total': len(indexed_files),
        'calculated': 0,
        'from_cache': 0,
        'errors': 0,
        'skipped': 0
    }

    print(f"Вычисление хэшей ({algorithm})...")
    print(f"Всего файлов для проверки: {len(indexed_files)}")

    for i, file_data in enumerate(indexed_files, 1):
        relative_path = file_data['relative_path']
        file_id = file_data['id']

        # Проверяем, есть ли уже хэш в БД (если не force_recalculate)
        if not force_recalculate:
            cursor.execute("""
                SELECT hash_value FROM file_hashes 
                WHERE file_id = ? AND hash_algorithm = ?
            """, (file_id, algorithm))

            existing_hash = cursor.fetchone()

            if existing_hash:
                stats['from_cache'] += 1
                if i % 50 == 0 or i == len(indexed_files):
                    print(f"  Прогресс: {i}/{len(indexed_files)} (из кэша: {stats['from_cache']})")
                continue

        # Вычисляем хэш
        absolute_path = os.path.join(folder_path, relative_path)
        hash_value = calculate_file_hash(absolute_path, algorithm)

        if hash_value is None:
            stats['errors'] += 1
            continue

        # Сохраняем в БД
        if existing_hash:
            # Обновляем существующий хэш
            cursor.execute("""
                UPDATE file_hashes 
                SET hash_value = ?, calculated_at = ?
                WHERE file_id = ? AND hash_algorithm = ?
            """, (hash_value, now, file_id, algorithm))
        else:
            # Добавляем новый хэш
            cursor.execute("""
                INSERT INTO file_hashes (file_id, hash_algorithm, hash_value, calculated_at)
                VALUES (?, ?, ?, ?)
            """, (file_id, algorithm, hash_value, now))

        stats['calculated'] += 1

        # Прогресс каждые 50 файлов или последний
        if i % 50 == 0 or i == len(indexed_files):
            print(f"  Прогресс: {i}/{len(indexed_files)} "
                  f"(посчитано: {stats['calculated']}, "
                  f"из кэша: {stats['from_cache']}, "
                  f"ошибок: {stats['errors']})")

    # Сохраняем изменения
    db.connection.commit()

    return stats


import os  # Добавим в начало файла, если нужно