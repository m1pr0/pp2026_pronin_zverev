from back.database import engine
from back.models import DatabaseBase, RegisteredUser, UserRating
from sqlalchemy import text, inspect

def add_profile_columns_if_not_exists():
    """Добавляет колонки анкеты в таблицу registered_users, если они не существуют."""
    with engine.connect() as conn:
        # Получаем информацию о колонках таблицы
        inspector = inspect(engine)
        columns = inspector.get_columns("registered_users")
        column_names = [col["name"] for col in columns]
        
        # Проверяем и добавляем недостающие колонки
        new_columns = []
        if "gender" not in column_names:
            new_columns.append("gender")
        if "age" not in column_names:
            new_columns.append("age")
        if "profession" not in column_names:
            new_columns.append("profession")
        
        # Если есть новые колонки, добавляем их через ALTER TABLE
        if new_columns:
            for col in new_columns:
                if col == "age":
                    sql = text("ALTER TABLE registered_users ADD COLUMN age INTEGER")
                else:
                    sql = text(f"ALTER TABLE registered_users ADD COLUMN {col} VARCHAR")
                conn.execute(sql)
                print(f"Добавлена колонка: {col}")
            conn.commit()
            print("Колонки профиля успешно добавлены!")
        else:
            print("Все колонки профиля уже существуют.")

if __name__ == "__main__":
    print("Создание новых таблиц...")
    
    # Сначала создаем таблицы, если их нет
    DatabaseBase.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы!")
    
    # Затем добавляем колонки профиля, если они не существуют
    add_profile_columns_if_not_exists()
    print("Готово!")
