"""
Тестовый скрипт для проверки работы сервисов рекомендаций.
Запуск: python test_services.py
"""

from sqlalchemy.orm import Session
from back.database import SessionLocal, engine
from back.models import Base
from back import genre_recommendation_service
from back import profile_recommendation_service
from back.genres import get_all_genres, decode_genres

# Создаём таблицы (если не существуют)
Base.metadata.create_all(bind=engine)


def test_genres():
    """Тест 1: Получение списка жанров."""
    print("\n" + "=" * 60)
    print(" ТЕСТ 1: Список жанров")
    print("=" * 60)
    
    genres = get_all_genres()
    print(f"\n✅ Доступно жанров: {len(genres)}")
    for code, name in list(genres.items())[:5]:
        print(f"  {code} → {name}")
    print("  ...")


def test_genre_recommendations():
    """Тест 2: Рекомендации по жанрам."""
    print("\n" + "=" * 60)
    print(" ТЕСТ 2: Рекомендации по жанрам (Action + Drama)")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        movies = genre_recommendation_service.get_movies_by_genres(
            db=db,
            genre_names=["Action", "Drama"],
            limit=5,
            sort_by="rating"
        )
        
        print(f"\n✅ Найдено фильмов: {len(movies)}")
        for i, movie in enumerate(movies, 1):
            print(f"\n  {i}. {movie.movie_title}")
            print(f"     Жанры: {', '.join(movie.genres)}")
            print(f"     Рейтинг: {movie.avg_rating} ({movie.rating_count} оценок)")
    finally:
        db.close()


def test_profile_recommendations():
    """Тест 3: Рекомендации по профилю."""
    print("\n" + "=" * 60)
    print(" ТЕСТ 3: Рекомендации по профилю (Male, 25, occupation=14)")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        movies = profile_recommendation_service.get_recommendations_by_profile(
            db=db,
            gender=True,
            age=25,
            occupation_label=14,
            top_k=10,
            top_n=5
        )
        
        print(f"\n✅ Рекомендаций: {len(movies)}")
        for i, movie in enumerate(movies, 1):
            print(f"\n  {i}. {movie.movie_title}")
            print(f"     Жанры: {', '.join(movie.genres)}")
            print(f"     Прогноз оценки: {movie.predicted_rating}")
            print(f"     Скор рекомендации: {movie.recommendation_score}")
    finally:
        db.close()


def test_decode_genres():
    """Тест 4: Декодирование жанров."""
    print("\n" + "=" * 60)
    print(" ТЕСТ 4: Декодирование жанров")
    print("=" * 60)
    
    test_cases = [
        "0, 7",
        "4",
        "10, 15",
        "0, 4, 7, 15"
    ]
    
    for case in test_cases:
        decoded = decode_genres(case)
        print(f"\n  '{case}' → {decoded}")


if __name__ == "__main__":
    print("\n" + "🎬" * 30)
    print("ТЕСТИРОВАНИЕ СЕРВИСОВ РЕКОМЕНДАЦИЙ")
    print("🎬" * 30)
    
    try:
        test_genres()
        test_decode_genres()
        test_genre_recommendations()
        test_profile_recommendations()
        
        print("\n" + "=" * 60)
        print(" ✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
