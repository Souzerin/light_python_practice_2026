"""
Модуль с фильтрами для отбора файлов при сканировании.
Каждый фильтр — функция, принимающая словарь с метаданными файла и возвращающая bool.
"""


def filter_by_extension(extensions):
    """
    Создает фильтр по расширениям файлов.

    Args:
        extensions: Список расширений (с точкой, например ['.py', '.txt'])

    Returns:
        Функцию-фильтр
    """
    extensions = [ext.lower() for ext in extensions]

    def _filter(file_data):
        return file_data.get('extension', '') in extensions

    return _filter


def filter_by_name_pattern(pattern):
    """
    Создает фильтр по имени файла (поиск подстроки без учета регистра).

    Args:
        pattern: Подстрока для поиска в имени файла

    Returns:
        Функцию-фильтр
    """
    pattern = pattern.lower()

    def _filter(file_data):
        return pattern in file_data.get('file_name', '').lower()

    return _filter


def filter_exclude_extensions(extensions):
    """
    Создает фильтр для исключения файлов по расширениям.

    Args:
        extensions: Список расширений для исключения

    Returns:
        Функцию-фильтр
    """
    extensions = [ext.lower() for ext in extensions]

    def _filter(file_data):
        return file_data.get('extension', '') not in extensions

    return _filter


def filter_by_min_size(min_bytes):
    """
    Создает фильтр по минимальному размеру файла.

    Args:
        min_bytes: Минимальный размер в байтах

    Returns:
        Функцию-фильтр
    """

    def _filter(file_data):
        return file_data.get('size_bytes', 0) >= min_bytes

    return _filter


def filter_by_max_size(max_bytes):
    """
    Создает фильтр по максимальному размеру файла.

    Args:
        max_bytes: Максимальный размер в байтах

    Returns:
        Функцию-фильтр
    """

    def _filter(file_data):
        return file_data.get('size_bytes', 0) <= max_bytes

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