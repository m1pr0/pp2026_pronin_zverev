from back.database import engine, Base
from back.models import RegisteredUser, UserRating

if __name__ == "__main__":
    print("Создание новых таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Новые таблицы успешно созданы!")