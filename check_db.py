"""Проверка базы данных"""
import sqlite3
import os

db_path = os.path.join("data", "app.db")

if not os.path.exists(db_path):
    print(f"❌ Файл БД не найден: {db_path}")
    exit(1)

print(f"✓ Файл БД найден: {db_path}")
print(f"  Размер: {os.path.getsize(db_path)} байт")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Получаем список таблиц
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print(f"\nТаблицы в БД ({len(tables)} шт.):")
for table in tables:
    print(f"  ✓ {table[0]}")
    # Показываем структуру
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"      - {col[1]} ({col[2]})")

conn.close()
print("\n✓ Проверка завершена")