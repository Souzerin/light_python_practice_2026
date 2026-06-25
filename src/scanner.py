"""
Модуль для рекурсивного сканирования папок.
Собирает метаданные файлов: путь, размер, дату изменения, тип.
"""

import os
from pathlib import Path
from datetime import datetime


def scan_folder(folder_path, filters=None):
    """
    Рекурсивно обходит папку и собирает метаданные файлов.

    Args:
        folder_path: Абсолютный путь к сканируемой папке
        filters: Список функций-фильтров (принимают словарь с метаданными, возвращают bool)

    Returns:
        Список словарей с метаданными файлов
    """
    files_data = []
    folder_path = os.path.abspath(folder_path)

    print(f"Сканирование папки: {folder_path}")
    file_count = 0
    error_count = 0

    for root, dirs, files in os.walk(folder_path):
        # Пропускаем скрытые папки (начинаются с точки)
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in files:
            # Пропускаем скрытые файлы
            if filename.startswith('.'):
                continue

            file_path = os.path.join(root, filename)

            try:
                # Получаем метаданные
                stat_info = os.stat(file_path)

                # Относительный путь от корня сканирования
                relative_path = os.path.relpath(file_path, folder_path)

                # Определяем расширение и тип файла
                extension = os.path.splitext(filename)[1].lower()
                file_type = get_file_type(extension)

                file_data = {
                    'relative_path': relative_path,
                    'file_name': filename,
                    'extension': extension if extension else '',
                    'size_bytes': stat_info.st_size,
                    'modified_at': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'file_type': file_type
                }

                # Применяем фильтры
                if filters:
                    passed = all(f(file_data) for f in filters)
                    if not passed:
                        continue

                files_data.append(file_data)
                file_count += 1

            except (PermissionError, OSError) as e:
                error_count += 1
                print(f"  ⚠ Пропущен (нет доступа): {relative_path}")
                continue

    print(f"✓ Сканирование завершено: найдено {file_count} файлов")
    if error_count > 0:
        print(f"  Пропущено из-за ошибок: {error_count}")

    return files_data


def get_file_type(extension):
    """
    Определяет тип файла по расширению.

    Args:
        extension: Расширение файла (с точкой)

    Returns:
        Строка с типом файла
    """
    type_map = {
        # Текстовые
        '.txt': 'text',
        '.md': 'text',
        '.csv': 'text',
        '.log': 'text',
        '.py': 'text',
        '.js': 'text',
        '.html': 'text',
        '.css': 'text',
        '.json': 'text',
        '.xml': 'text',
        '.yaml': 'text',
        '.yml': 'text',
        '.ini': 'text',
        '.cfg': 'text',

        # Изображения
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.svg': 'image',
        '.ico': 'image',

        # Документы
        '.pdf': 'document',
        '.doc': 'document',
        '.docx': 'document',
        '.xls': 'document',
        '.xlsx': 'document',
        '.ppt': 'document',
        '.pptx': 'document',

        # Архивы
        '.zip': 'archive',
        '.rar': 'archive',
        '.7z': 'archive',
        '.tar': 'archive',
        '.gz': 'archive',

        # Аудио
        '.mp3': 'audio',
        '.wav': 'audio',
        '.flac': 'audio',
        '.aac': 'audio',

        # Видео
        '.mp4': 'video',
        '.avi': 'video',
        '.mkv': 'video',
        '.mov': 'video',

        # Исполняемые
        '.exe': 'executable',
        '.dll': 'executable',
        '.so': 'executable',
        '.dylib': 'executable',
    }

    return type_map.get(extension, 'other')