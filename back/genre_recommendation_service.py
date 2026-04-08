"""
Сервис рекомендаций по жанрам.
Фильтрует фильмы по выбранным жанрам и сортирует по рейтингу/популярности.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from back.models import Movie, Rating
from back.genres import decode_genres, encode_genres, get_all_genres, GENRE_MAPPING
from typing import Optional
from pydantic import BaseModel


class GenreMovieResponse(BaseModel):
    movie_id: int
    movie_title: str
    genres: list[str]
    poster_url: Optional[str]
    avg_rating: Optional[float]
    rating_count: int


def get_available_genres() -> dict[int, str]:
    """Возвращает список доступных жанров."""
    return get_all_genres()


def get_movies_by_genres(
    db: Session,
    genre_names: list[str],
    limit: int = 20,
    sort_by: str = "rating"  # "rating" или "popularity"
) -> list[GenreMovieResponse]:
    """
    Возвращает фильмы по выбранным жанрам.
    
    :param genre_names: Список названий жанров (например, ["Action", "Drama"])
    :param limit: Максимальное количество фильмов
    :param sort_by: Сортировка - "rating" (средний рейтинг) или "popularity" (количество оценок)
    """
    # Кодируем жанры в коды
    genre_codes = encode_genres(genre_names)
    
    if not genre_codes:
        return []
    
    # Запрос: фильмы хотя бы с одним из выбранных жанров
    # movie_genres хранится как строка "0, 7" - используем LIKE для поиска
    query = db.query(
        Movie.movie_id,
        Movie.movie_title,
        Movie.movie_genres,
        Movie.poster_url,
        func.avg(Rating.user_rating).label("avg_rating"),
        func.count(Rating.user_id).label("rating_count")
    ).join(
        Rating, Movie.movie_id == Rating.movie_id, isouter=True
    )
    
    # Фильтр по жанрам (LIKE для каждого кода)
    genre_filters = [Movie.movie_genres.like(f"%{code}%") for code in genre_codes]
    query = query.filter(or_(*genre_filters))
    
    # Группировка
    query = query.group_by(Movie.movie_id)
    
    # Сортировка
    if sort_by == "rating":
        query = query.order_by(func.avg(Rating.user_rating).desc())
    else:  # popularity
        query = query.order_by(func.count(Rating.user_id).desc())
    
    # Лимит
    movies = query.limit(limit).all()
    
    # Формируем ответ
    result = []
    for row in movies:
        genres_list = decode_genres(row.movie_genres)
        result.append(
            GenreMovieResponse(
                movie_id=row.movie_id,
                movie_title=row.movie_title,
                genres=genres_list,
                poster_url=row.poster_url,
                avg_rating=round(row.avg_rating, 2) if row.avg_rating else None,
                rating_count=row.rating_count
            )
        )
    
    return result
