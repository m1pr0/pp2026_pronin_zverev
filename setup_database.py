"""
Скрипт для настройки базы данных movie_recommender
Запуск: python setup_database.py
"""

import psycopg2
from psycopg2 import sql, OperationalError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import os
import sys
import traceback

# ========== КОНФИГУРАЦИЯ ==========
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'movie_recommender',      # системная БД для первого подключения
    'user': 'postgres',
    'password': 'mipro777'               # ПОПРОБУЙТЕ ПУСТОЙ ПАРОЛЬ СНАЧАЛА
}

NEW_DB_NAME = 'movie_recommender'

# Пути к CSV файлам (исправьте под свои)
DATA_PATHS = {
    'movies': r'dataset/movies.csv',
    'users': r'dataset/users.csv',
    'ratings': r'dataset/ratings.csv'
}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def print_separator(title=""):
    """Печать разделителя"""
    print("\n" + "=" * 60)
    if title:
        print(f" {title}")
        print("=" * 60)

def print_success(msg):
    """Зелёное сообщение об успехе"""
    print(f"✅ {msg}")

def print_error(msg):
    """Красное сообщение об ошибке"""
    print(f"❌ {msg}")

def print_info(msg):
    """Синее информационное сообщение"""
    print(f"ℹ️ {msg}")

def print_warning(msg):
    """Жёлтое предупреждение"""
    print(f"⚠️ {msg}")

# ========== ШАГ 1: ПРОВЕРКА ОКРУЖЕНИЯ ==========
def check_environment():
    """Проверка окружения: Python, библиотеки, файлы"""
    print_separator("ШАГ 1: ПРОВЕРКА ОКРУЖЕНИЯ")
    
    # Python версия
    print_info(f"Python версия: {sys.version}")
    
    # Проверка библиотек
    libraries = ['psycopg2', 'sqlalchemy', 'pandas']
    for lib in libraries:
        try:
            __import__(lib)
            print_success(f"Библиотека {lib} установлена")
        except ImportError:
            print_error(f"Библиотека {lib} НЕ установлена")
            return False
    
    # Проверка CSV файлов
    print_info("Проверка CSV файлов:")
    all_files_exist = True
    for name, path in DATA_PATHS.items():
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print_success(f"  {name}: {full_path} ({size:,} байт)")
        else:
            print_error(f"  {name}: {full_path} - ФАЙЛ НЕ НАЙДЕН")
            all_files_exist = False
    
    return all_files_exist

# ========== ШАГ 2: ПРОВЕРКА POSTGRESQL ==========
def test_postgres_connection():
    """Тестирование подключения к PostgreSQL"""
    print_separator("ШАГ 2: ПРОВЕРКА ПОДКЛЮЧЕНИЯ К POSTGRESQL")

    password = DB_CONFIG['password']
    print_info(f"Пробуем пароль: '{password}'")
    print_info(f"Параметры: host={DB_CONFIG['host']}, port={DB_CONFIG['port']}, user={DB_CONFIG['user']}")

    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=password,
            connect_timeout=5
        )
        conn.close()
        print_success("Подключение успешно!")
        return True

    except OperationalError as e:
        error_msg = str(e)
        print_error(f"Ошибка подключения:")
        print(f"  Тип: OperationalError")
        print(f"  Сообщение: {error_msg}")
        print(f"  Args: {e.args}")
        print()
        print_info("Диагноз:")
        if "password authentication failed" in error_msg:
            print("  ❌ Неверный пароль — измените пароль в DB_CONFIG")
        elif "Connection refused" in error_msg or "could not connect" in error_msg:
            print("  ❌ PostgreSQL не запущен")
            print("     → services.msc → postgresql-x64-XX → Запустить")
        elif "no password supplied" in error_msg:
            print("  ❌ Сервер требует пароль")
            print("     → Укажите пароль в DB_CONFIG")
        elif "Invalid connection" in error_msg:
            print("  ❌ Проблема с подключением — проверьте, что PostgreSQL установлен")
        else:
            print("  ❌ Смотрите полное сообщение ошибки выше")
        return False

    except Exception as e:
        print_error(f"Неожиданная ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========== ШАГ 3: СОЗДАНИЕ БАЗЫ ДАННЫХ ==========
def create_database():
    """Создание базы данных"""
    print_separator("ШАГ 3: СОЗДАНИЕ БАЗЫ ДАННЫХ")
    
    if not DB_CONFIG['password']:
        print_error("Нет пароля для подключения")
        return False
    
    conn = None
    try:
        print_info(f"Подключение к PostgreSQL как {DB_CONFIG['user']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        print_success("Подключение установлено")
        
        # Проверяем существование БД
        print_info(f"Проверка существования БД '{NEW_DB_NAME}'...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (NEW_DB_NAME,))
        exists = cursor.fetchone()
        
        if exists:
            print_info(f"База данных '{NEW_DB_NAME}' уже существует")
        else:
            print_info(f"Создание БД '{NEW_DB_NAME}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(NEW_DB_NAME)))
            print_success(f"База данных '{NEW_DB_NAME}' создана")
        
        cursor.close()
        return True
        
    except OperationalError as e:
        print_error(f"Ошибка подключения: {e}")
        print_info("Проверьте:")
        print("  - Запущен ли PostgreSQL?")
        print("  - Правильный ли пароль?")
        return False
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()
            print_info("Соединение закрыто")

# ========== ШАГ 4: СОЗДАНИЕ ТАБЛИЦ ==========
def create_tables():
    """Создание таблиц"""
    print_separator("ШАГ 4: СОЗДАНИЕ ТАБЛИЦ")
    
    db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{NEW_DB_NAME}"
    print_info(f"Подключение к БД: {NEW_DB_NAME}")
    
    try:
        engine = create_engine(db_url, echo=False)
        print_success("Движок SQLAlchemy создан")
        
        create_tables_sql = """
        -- Таблица фильмов
        DROP TABLE IF EXISTS ratings CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP TABLE IF EXISTS movies CASCADE;

        CREATE TABLE movies (
            movie_id INTEGER PRIMARY KEY,
            movie_title TEXT NOT NULL,
            movie_genres TEXT,
            poster_url TEXT
        );

        -- Таблица пользователей
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            user_gender BOOLEAN,
            bucketized_user_age INTEGER,
            user_occupation_label INTEGER,
            user_occupation_text TEXT,
            user_zip_code VARCHAR(10)
        );

        -- Таблица оценок
        CREATE TABLE ratings (
            user_id INTEGER REFERENCES users(user_id),
            movie_id INTEGER REFERENCES movies(movie_id),
            user_rating FLOAT,
            timestamp INTEGER,
            PRIMARY KEY (user_id, movie_id)
        );

        -- Индексы
        CREATE INDEX idx_ratings_movie ON ratings(movie_id);
        CREATE INDEX idx_ratings_user ON ratings(user_id);
        CREATE INDEX idx_ratings_rating ON ratings(user_rating);
        """
        
        with engine.connect() as conn:
            print_info("Выполнение SQL запросов...")
            for i, statement in enumerate(create_tables_sql.split(';'), 1):
                if statement.strip():
                    print_info(f"  Запрос {i}...")
                    conn.execute(text(statement))
            conn.commit()
        
        print_success("Таблицы созданы")
        
        # Проверяем, что таблицы действительно создались
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('movies', 'users', 'ratings')
            """))
            tables = [row[0] for row in result]
            print_info(f"Созданные таблицы: {tables}")
        
        return True
        
    except SQLAlchemyError as e:
        print_error(f"Ошибка SQLAlchemy: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        traceback.print_exc()
        return False

# ========== ШАГ 5: ИМПОРТ CSV ==========
def import_csv_data():
    """Импорт данных из CSV"""
    print_separator("ШАГ 5: ИМПОРТ CSV ДАННЫХ")
    
    db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{NEW_DB_NAME}"
    engine = create_engine(db_url)
    
    # Проверка существования файлов с абсолютными путями
    abs_paths = {}
    for name, path in DATA_PATHS.items():
        abs_path = os.path.abspath(path)
        abs_paths[name] = abs_path
        if os.path.exists(abs_path):
            size = os.path.getsize(abs_path)
            print_success(f"Файл {name}: {abs_path} ({size:,} байт)")
        else:
            print_error(f"Файл {name}: {abs_path} - НЕ СУЩЕСТВУЕТ")
            return False
    
    try:
        # Импорт movies
        print_info("\nИмпорт movies...")
        movies_df = pd.read_csv(abs_paths['movies'])
        print_info(f"  Прочитано {len(movies_df)} строк")
        print_info(f"  Колонки: {list(movies_df.columns)}")
        movies_df.to_sql('movies', engine, if_exists='append', index=False)
        print_success(f"  Импортировано {len(movies_df)} фильмов")
        
        # Импорт users
        print_info("\nИмпорт users...")
        users_df = pd.read_csv(abs_paths['users'])
        print_info(f"  Прочитано {len(users_df)} строк")
        print_info(f"  Колонки: {list(users_df.columns)}")
        users_df.to_sql('users', engine, if_exists='append', index=False)
        print_success(f"  Импортировано {len(users_df)} пользователей")
        
        # Импорт ratings
        print_info("\nИмпорт ratings...")
        chunksize = 50000
        total = 0
        for i, chunk in enumerate(pd.read_csv(abs_paths['ratings'], chunksize=chunksize)):
            chunk.to_sql('ratings', engine, if_exists='append', index=False)
            total += len(chunk)
            print_info(f"  Часть {i+1}: импортировано {len(chunk)} строк (всего {total})")
        
        print_success(f"Всего импортировано {total} оценок")
        return True
        
    except Exception as e:
        print_error(f"Ошибка при импорте: {e}")
        traceback.print_exc()
        return False

# ========== ШАГ 6: ВЕРИФИКАЦИЯ ==========
def verify_data():
    """Проверка импортированных данных"""
    print_separator("ШАГ 6: ВЕРИФИКАЦИЯ ДАННЫХ")
    
    db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{NEW_DB_NAME}"
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # Считаем записи
            movies_count = conn.execute(text("SELECT COUNT(*) FROM movies")).scalar()
            users_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            ratings_count = conn.execute(text("SELECT COUNT(*) FROM ratings")).scalar()
            
            print_info("Статистика базы данных:")
            print(f"  🎬 Фильмы: {movies_count}")
            print(f"  👥 Пользователи: {users_count}")
            print(f"  ⭐ Оценки: {ratings_count}")
            
            # Пример данных
            if movies_count > 0:
                sample = conn.execute(text("SELECT movie_id, movie_title FROM movies LIMIT 3")).fetchall()
                print_info("\nПример фильмов:")
                for mid, title in sample:
                    print(f"  {mid}: {title[:50]}")
            
            return True
            
    except Exception as e:
        print_error(f"Ошибка верификации: {e}")
        return False

# ========== ОСНОВНОЙ БЛОК ==========
def main():
    print_separator("MOVIE RECOMMENDER - НАСТРОЙКА БД")
    print_info("Начинаем пошаговую настройку...")
    
    # Шаг 1: Проверка окружения
    if not check_environment():
        print_error("\n❌ ПРОВАЛ: Проблемы с окружением")
        print_info("Исправьте ошибки выше и запустите скрипт снова")
        return False
    
    # Шаг 2: Проверка PostgreSQL
    if not test_postgres_connection():
        print_error("\n❌ ПРОВАЛ: Не удалось подключиться к PostgreSQL")
        print_info("Решение:")
        print("  1. Откройте services.msc")
        print("  2. Найдите службу 'postgresql-x64-17'")
        print("  3. Запустите её, если остановлена")
        print("  4. Если не помогает - переустановите PostgreSQL")
        return False
    
    # Шаг 3: Создание БД
    if not create_database():
        print_error("\n❌ ПРОВАЛ: Не удалось создать БД")
        return False
    
    # Шаг 4: Создание таблиц
    if not create_tables():
        print_error("\n❌ ПРОВАЛ: Не удалось создать таблицы")
        return False
    
    # Шаг 5: Импорт данных
    if not import_csv_data():
        print_error("\n❌ ПРОВАЛ: Не удалось импортировать данные")
        return False
    
    # Шаг 6: Верификация
    verify_data()
    
    print_separator("ГОТОВО!")
    print_success("База данных успешно настроена!")
    print_info("Теперь можно запускать бэкенд: uvicorn backend.main:app --reload")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)