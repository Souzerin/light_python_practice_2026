import sqlite3
import os


class Database:
    """Класс для управления базой данных индексатора."""

    def initialize(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # создаём папку только если путь не пустой
            os.makedirs(db_dir, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self._create_tables()
        self.connection.commit()
    def initialize(self):
        """
        Инициализация базы данных: создание папки, подключение, создание таблиц.
        """
        # Создание директории для БД, если не существует
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Подключение к БД
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

        # Создание таблиц
        self._create_tables()

        # Применение изменений
        self.connection.commit()

    def _create_tables(self):
        """
        Создание начальной схемы таблиц для индексации файлов.
        """
        # Таблица для хранения информации о файлах
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                relative_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                extension TEXT,
                size_bytes INTEGER,
                modified_at TEXT,
                file_type TEXT,
                is_present INTEGER DEFAULT 1
            )
        """)

        # Таблица для хранения хэшей файлов (для этапа 3)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                hash_algorithm TEXT NOT NULL DEFAULT 'sha256',
                hash_value TEXT NOT NULL,
                calculated_at TEXT NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # Таблица для хранения результатов проверок (для этапа 4)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_type TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                checked_at TEXT NOT NULL,
                result_summary TEXT
            )
        """)

        # Таблица для хранения деталей проверок
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id INTEGER NOT NULL,
                file_id INTEGER,
                relative_path TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (check_id) REFERENCES check_results(id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL
            )
        """)

    def close(self):
        """Закрытие соединения с базой данных."""
        if self.connection:
            self.connection.close()