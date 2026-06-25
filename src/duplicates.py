"""
Модуль для поиска дубликатов файлов по хэшу содержимого.
"""

import os
from datetime import datetime


def find_duplicates(db, algorithm='sha256', min_group_size=2):
    """
    Находит группы файлов с одинаковым хэшем.

    Args:
        db: Объект Database с активным соединением
        algorithm: Алгоритм хэширования
        min_group_size: Минимальный размер группы для включения в отчет

    Returns:
        Список групп дубликатов, каждая группа - список словарей с информацией о файлах
    """
    cursor = db.cursor

    # Ищем группы файлов с одинаковым хэшем
    cursor.execute("""
        SELECT 
            fh.hash_value,
            COUNT(*) as file_count,
            SUM(f.size_bytes) as total_size
        FROM file_hashes fh
        JOIN files f ON fh.file_id = f.id
        WHERE fh.hash_algorithm = ?
            AND f.is_present = 1
        GROUP BY fh.hash_value
        HAVING COUNT(*) >= ?
        ORDER BY file_count DESC, total_size DESC
    """, (algorithm, min_group_size))

    duplicate_groups = []

    for row in cursor.fetchall():
        hash_value = row[0]
        file_count = row[1]
        total_size = row[2]

        # Получаем детальную информацию о файлах в группе
        cursor.execute("""
            SELECT 
                f.id,
                f.relative_path,
                f.size_bytes,
                f.modified_at,
                f.file_type
            FROM files f
            JOIN file_hashes fh ON f.id = fh.file_id
            WHERE fh.hash_value = ?
                AND fh.hash_algorithm = ?
                AND f.is_present = 1
            ORDER BY f.relative_path
        """, (hash_value, algorithm))

        files_in_group = []
        for file_row in cursor.fetchall():
            files_in_group.append({
                'id': file_row[0],
                'relative_path': file_row[1],
                'size_bytes': file_row[2],
                'modified_at': file_row[3],
                'file_type': file_row[4]
            })

        duplicate_groups.append({
            'hash': hash_value,
            'file_count': file_count,
            'total_size': total_size,
            'files': files_in_group
        })

    return duplicate_groups


def find_duplicates_by_size(db, min_group_size=2):
    """
    Быстрый предварительный поиск потенциальных дубликатов по размеру.
    Полезно для больших папок перед вычислением хэшей.

    Args:
        db: Объект Database с активным соединением
        min_group_size: Минимальный размер группы

    Returns:
        Список групп файлов с одинаковым размером (потенциальные дубликаты)
    """
    cursor = db.cursor

    cursor.execute("""
        SELECT 
            size_bytes,
            COUNT(*) as file_count,
            GROUP_CONCAT(relative_path, ' | ') as files_list
        FROM files
        WHERE is_present = 1
            AND size_bytes > 0
        GROUP BY size_bytes
        HAVING COUNT(*) >= ?
        ORDER BY file_count DESC, size_bytes DESC
    """, (min_group_size,))

    return [
        {
            'size_bytes': row[0],
            'file_count': row[1],
            'files': row[2].split(' | ') if row[2] else []
        }
        for row in cursor.fetchall()
    ]


def get_duplicate_stats(duplicate_groups):
    """
    Вычисляет общую статистику по дубликатам.

    Args:
        duplicate_groups: Результат find_duplicates()

    Returns:
        Словарь со статистикой
    """
    total_groups = len(duplicate_groups)
    total_files = sum(g['file_count'] for g in duplicate_groups)
    wasted_space = sum(g['total_size'] * (g['file_count'] - 1) for g in duplicate_groups)

    # Распределение по размерам групп
    group_sizes = {}
    for g in duplicate_groups:
        size = g['file_count']
        group_sizes[size] = group_sizes.get(size, 0) + 1

    return {
        'total_groups': total_groups,
        'total_duplicate_files': total_files,
        'wasted_space_bytes': wasted_space,
        'group_sizes': group_sizes
    }