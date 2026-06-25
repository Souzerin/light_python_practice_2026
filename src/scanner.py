"""
Модуль для рекурсивного сканирования папок.
Собирает метаданные файлов: путь, размер, дату изменения, тип.
"""

import os
from datetime import datetime


def scan_folder(folder_path, filters=None):
    """
    Рекурсивно обходит папку и собирает метаданные файлов.
    Использует явную рекурсию через внутреннюю функцию.

    Args:
        folder_path: Абсолютный путь к сканируемой папке
        filters: Список функций-фильтров (принимают словарь с метаданными, возвращают bool)

    Returns:
        Список словарей с метаданными файлов
    """
    files_data = []
    folder_path = os.path.abspath(folder_path)
    error_count = 0

    print(f"Сканирование папки: {folder_path}")

    def _recursive_scan(current_path):
        """Рекурсивная функция обхода."""
        nonlocal error_count

        try:
            # Получаем содержимое текущей папки
            entries = os.listdir(current_path)
        except (PermissionError, OSError) as e:
            error_count += 1
            rel_path = os.path.relpath(current_path, folder_path)
            print(f"  ⚠ Пропущена папка (нет доступа): {rel_path}")
            return

        for entry in entries:
            # Пропускаем скрытые файлы и папки
            if entry.startswith('.'):
                continue

            entry_path = os.path.join(current_path, entry)

            try:
                if os.path.isdir(entry_path):
                    # РЕКУРСИВНЫЙ ВЫЗОВ ДЛЯ ПАПКИ
                    _recursive_scan(entry_path)

                elif os.path.isfile(entry_path):
                    # Обработка файла
                    stat_info = os.stat(entry_path)
                    relative_path = os.path.relpath(entry_path, folder_path)
                    extension = os.path.splitext(entry)[1].lower()
                    file_type = get_file_type(extension)

                    file_data = {
                        'relative_path': relative_path,
                        'file_name': entry,
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

            except (PermissionError, OSError) as e:
                error_count += 1
                rel_path = os.path.relpath(entry_path, folder_path)
                print(f"  ⚠ Пропущен (нет доступа): {rel_path}")
                continue

    # Запускаем рекурсивный обход с корневой папки
    _recursive_scan(folder_path)

    print(f"✓ Сканирование завершено: найдено {len(files_data)} файлов")
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