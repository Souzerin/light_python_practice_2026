"""
Модуль с фильтрами для отбора файлов при сканировании.
Каждый фильтр — функция, принимающая словарь с метаданными файла и возвращающая bool.
"""


def filter_by_extension(extensions):
    """Фильтр по расширениям файлов."""
    extensions = [ext.lower() for ext in extensions]

    def _filter(file_data):
        return file_data.get('extension', '') in extensions

    return _filter


def filter_by_name_pattern(pattern):
    """Фильтр по подстроке в имени файла."""
    pattern = pattern.lower()

    def _filter(file_data):
        return pattern in file_data.get('file_name', '').lower()

    return _filter


def filter_exclude_extensions(extensions):
    """Исключает файлы с указанными расширениями."""
    extensions = [ext.lower() for ext in extensions]

    def _filter(file_data):
        return file_data.get('extension', '') not in extensions

    return _filter


def filter_by_min_size(min_bytes):
    """Фильтр по минимальному размеру."""

    def _filter(file_data):
        return file_data.get('size_bytes', 0) >= min_bytes

    return _filter


def filter_by_max_size(max_bytes):
    """Фильтр по максимальному размеру."""

    def _filter(file_data):
        return file_data.get('size_bytes', 0) <= max_bytes

    return _filter


def filter_by_size_range(min_bytes, max_bytes):
    """Фильтр по диапазону размера."""

    def _filter(file_data):
        size = file_data.get('size_bytes', 0)
        return min_bytes <= size <= max_bytes

    return _filter


# Предустановленные фильтры
def filter_text_only(file_data):
    """Только текстовые файлы."""
    return file_data.get('file_type') == 'text'


def filter_media_only(file_data):
    """Только медиафайлы (изображения, аудио, видео)."""
    return file_data.get('file_type') in ('image', 'audio', 'video')


def filter_python_only(file_data):
    """Только Python файлы."""
    return file_data.get('extension') == '.py'


def filter_images_only(file_data):
    """Только изображения."""
    return file_data.get('file_type') == 'image'


def filter_documents_only(file_data):
    """Только документы."""
    return file_data.get('file_type') == 'document'


def filter_no_extension(file_data):
    """Файлы без расширения."""
    return file_data.get('extension') == ''