"""
Сервис рекомендаций по профилю пользователя (k-NN).
Находит похожих пользователей и рекомендует фильмы, которые они оценили высоко.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from back.models import User, Movie, Rating
from back.genres import decode_genres
from typing import Optional
from pydantic import BaseModel
import math


class ProfileRecommendationRequest(BaseModel):
    gender: bool  # True = Male, False = Female
    age: int
    occupation_label: int
    top_k: int = 10  # Количество похожих пользователей
    top_n: int = 20  # Количество рекомендаций


class ProfileMovieResponse(BaseModel):
    movie_id: int
    movie_title: str
    genres: list[str]
    poster_url: Optional[str]
    predicted_rating: float
    recommendation_score: float


def _calculate_similarity(
    user1: User,
    user2: User
) -> float:
    """
    Вычисляет похожесть между двумя пользователями.
    Используем упрощённую метрику:
    - Пол: 0 или 1 (совпадает/не совпадает)
    - Возраст: нормализованная разница (чем ближе, тем лучше)
    - Профессия: 0 или 1 (совпадает/не совпадает)
    
    Возвращает значение от 0 до 1 (1 = максимально похожи)
    """
    # Весовые коэффициенты
    w_gender = 0.2
    w_age = 0.3
    w_occupation = 0.5
    
    # Похожесть по полу (0 или 1)
    gender_sim = 1.0 if user1.user_gender == user2.user_gender else 0.0
    
    # Похожесть по возрасту (нормализуем по диапазону 0-100)
    age_diff = abs((user1.bucketized_user_age or 0) - (user2.bucketized_user_age or 0))
    age_sim = max(0, 1.0 - age_diff / 50.0)  # Разница в 50+ лет = 0
    
    # Похожесть по профессии
    occupation_sim = 1.0 if user1.user_occupation_label == user2.user_occupation_label else 0.0
    
    # Взвешенная сумма
    similarity = (
        w_gender * gender_sim +
        w_age * age_sim +
        w_occupation * occupation_sim
    )
    
    return similarity


def find_similar_users(
    db: Session,
    target_user: dict,  # {"gender": bool, "age": int, "occupation_label": int}
    top_k: int = 10
) -> list[User]:
    """
    Находит top_k похожих пользователей из БД.
    """
    # Создаём фиктивного пользователя для сравнения
    target = User(
        user_id=-1,
        user_gender=target_user["gender"],
        bucketized_user_age=target_user["age"],
        user_occupation_label=target_user["occupation_label"]
    )
    
    # Загружаем всех пользователей (кэшируем в памяти)
    all_users = db.query(User).all()
    
    # Вычисляем похожесть для каждого
    users_with_similarity = []
    for user in all_users:
        sim = _calculate_similarity(target, user)
        users_with_similarity.append((user, sim))
    
    # Сортируем по убыванию похожести
    users_with_similarity.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем top_k
    return [user for user, sim in users_with_similarity[:top_k]]


def get_recommendations_by_profile(
    db: Session,
    gender: bool,
    age: int,
    occupation_label: int,
    top_k: int = 10,
    top_n: int = 20,
    exclude_seen: bool = True
) -> list[ProfileMovieResponse]:
    """
    Возвращает рекомендации для пользователя с заданным профилем.
    
    :param gender: Пол пользователя
    :param age: Возраст
    :param occupation_label: Код профессии
    :param top_k: Количество похожих пользователей для поиска
    :param top_n: Количество рекомендаций
    :param exclude_seen: Исключать ли уже оценённые фильмы
    """
    # Находим похожих пользователей
    similar_users = find_similar_users(
        db,
        {"gender": gender, "age": age, "occupation_label": occupation_label},
        top_k
    )
    
    if not similar_users:
        return []
    
    # Получаем ID похожих пользователей
    similar_user_ids = [user.user_id for user in similar_users]
    
    # Загружаем их оценки
    ratings = db.query(Rating).filter(
        Rating.user_id.in_(similar_user_ids)
    ).all()
    
    # Агрегируем: для каждого фильма считаем средневзвешенную оценку
    movie_scores = {}  # movie_id -> {"weighted_sum": float, "sim_sum": float}
    
    for rating in ratings:
        # Находим похожесть этого пользователя
        user = next((u for u in similar_users if u.user_id == rating.user_id), None)
        if not user:
            continue
        
        sim = _calculate_similarity(
            User(
                user_id=-1,
                user_gender=gender,
                bucketized_user_age=age,
                user_occupation_label=occupation_label
            ),
            user
        )
        
        if rating.movie_id not in movie_scores:
            movie_scores[rating.movie_id] = {"weighted_sum": 0, "sim_sum": 0}
        
        movie_scores[rating.movie_id]["weighted_sum"] += rating.user_rating * sim
        movie_scores[rating.movie_id]["sim_sum"] += sim
    
    # Вычисляем итоговый скор
    movie_recommendations = []
    for movie_id, scores in movie_scores.items():
        if scores["sim_sum"] == 0:
            continue
        
        predicted_rating = scores["weighted_sum"] / scores["sim_sum"]
        
        movie_recommendations.append({
            "movie_id": movie_id,
            "predicted_rating": round(predicted_rating, 2),
            "recommendation_score": round(predicted_rating * scores["sim_sum"], 2)
        })
    
    # Сортируем по predicted_rating
    movie_recommendations.sort(key=lambda x: x["predicted_rating"], reverse=True)
    
    # Берём top_n
    top_movies = movie_recommendations[:top_n]
    
    # Загружаем информацию о фильмах
    movie_ids = [m["movie_id"] for m in top_movies]
    movies = db.query(Movie).filter(Movie.movie_id.in_(movie_ids)).all()
    movies_dict = {movie.movie_id: movie for movie in movies}
    
    # Формируем ответ
    result = []
    for rec in top_movies:
        movie = movies_dict.get(rec["movie_id"])
        if not movie:
            continue
        
        result.append(
            ProfileMovieResponse(
                movie_id=movie.movie_id,
                movie_title=movie.movie_title,
                genres=decode_genres(movie.movie_genres),
                poster_url=movie.poster_url,
                predicted_rating=rec["predicted_rating"],
                recommendation_score=rec["recommendation_score"]
            )
        )
    
    return result
