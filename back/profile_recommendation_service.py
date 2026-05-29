"""
Сервис рекомендаций по профилю пользователя (k-NN).
Находит похожих пользователей и рекомендует фильмы, которые они оценили высоко.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from back.models import User, Movie, Rating, RegisteredUser, UserRating
from back.genres import decode_genres
from typing import Optional, List, Dict, Any


def _calculate_similarity_profile(
    profile1: Dict[str, Any], profile2: Dict[str, Any]
) -> float:
    """
    Вычисляет похожесть между двумя профилями (dict).
    
    :param profile1: {"gender": Optional[bool], "age": Optional[int], "occupation_label": Optional[int]}
    :param profile2: {"gender": Optional[bool], "age": Optional[int], "occupation_label": Optional[int]}
    :return: float от 0 до 1
    """
    w_gender = 0.2
    w_age = 0.3
    w_occupation = 0.5
    
    # Похожесть по полу
    gender_sim = 1.0
    if profile1.get("gender") is not None and profile2.get("gender") is not None:
        gender_sim = 1.0 if profile1["gender"] == profile2["gender"] else 0.0
    
    # Похожесть по возрасту
    age_sim = 1.0
    if profile1.get("age") is not None and profile2.get("age") is not None:
        age_diff = abs(profile1["age"] - profile2["age"])
        age_sim = max(0, 1.0 - age_diff / 50.0)
    
    # Похожесть по профессии
    occupation_sim = 1.0
    if profile1.get("occupation_label") is not None and profile2.get("occupation_label") is not None:
        occupation_sim = 1.0 if profile1["occupation_label"] == profile2["occupation_label"] else 0.0
    
    return w_gender * gender_sim + w_age * age_sim + w_occupation * occupation_sim


def find_similar_users(
    db: Session,
    target_user: Dict[str, Any],  # {"gender": Optional[bool], "age": Optional[int], "occupation_label": Optional[int]}
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Находит top_k похожих пользователей из БД.
    Параметры могут быть None - в этом случае они игнорируются в расчете схожести.
    
    Возвращает список словарей с профилем пользователя для совместимости с новой логикой.
    """
    # Загружаем всех пользователей из старой таблицы (для совместимости с датасетом)
    all_users = db.query(User).all()
    
    users_with_similarity = []
    for user in all_users:
        # Создаем профиль пользователя из БД
        user_profile = {
            "gender": user.user_gender,
            "age": user.bucketized_user_age,
            "occupation_label": user.user_occupation_label
        }
        
        sim = _calculate_similarity_profile(target_user, user_profile)
        users_with_similarity.append((user, sim))
    
    users_with_similarity.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем список кортежей (user, similarity)
    return [(user, sim) for user, sim in users_with_similarity[:top_k]]


def find_similar_users_from_ratings(
    db: Session,
    target_user: Dict[str, Any],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Находит top_k похожих пользователей на основе оценок из ratings.csv.
    Использует UserRating для поиска пользователей, которые оценили те же фильмы.
    """
    # Получаем ID всех пользователей, которые оценили фильмы
    rated_user_ids = db.query(UserRating.user_id).distinct().all()
    rated_user_ids = [r[0] for r in rated_user_ids]
    
    users_with_similarity = []
    for uid in rated_user_ids:
        # Создаем профиль пользователя из UserRating
        # Для упрощения берем только пол, возраст и профессию из RegisteredUser
        user_profile = {
            "gender": None,
            "age": None,
            "occupation_label": None
        }
        
        # Пытаемся получить данные из RegisteredUser
        registered_user = db.query(RegisteredUser).filter(RegisteredUser.id == uid).first()
        if registered_user:
            if registered_user.gender:
                user_profile["gender"] = registered_user.gender.lower() == "male"
            user_profile["age"] = registered_user.age
            # Простое сопоставление профессии с целым числом
            if registered_user.profession:
                profession_to_int = {
                    "academic/teacher": 0,
                    "artist": 1,
                    "clerk/admin": 2,
                    "student": 3,
                    "customer_service": 4,
                    "medical": 5,
                    "executive/manager": 6,
                    "farmer": 7,
                    "homemaker": 8,
                    "journalist": 9,
                    "lawyer": 10,
                    "programmer": 11,
                    "retired": 12,
                    "sales/marketing": 13,
                    "scientist": 14,
                    "self-employed": 15,
                    "technician/engineer": 16,
                    "worker/craftsman": 17,
                    "unemployed": 18,
                    "writer": 19,
                    "other": 20
                }
                user_profile["occupation_label"] = profession_to_int.get(registered_user.profession, 20)
        
        sim = _calculate_similarity_profile(target_user, user_profile)
        users_with_similarity.append((uid, sim))
    
    users_with_similarity.sort(key=lambda x: x[1], reverse=True)
    
    return users_with_similarity[:top_k]


def get_recommendations_by_profile(
    db: Session,
    gender: Optional[bool] = None,
    age: Optional[int] = None,
    occupation_label: Optional[int] = None,
    top_k: int = 10,
    top_n: int = 20,
    exclude_seen: bool = True,
    use_ratings_dataset: bool = True  # Использовать оценки из ratings.csv
) -> List[Dict[str, Any]]:
    """
    Возвращает рекомендации для пользователя с заданным профилем.
    
    :param gender: Пол пользователя (Optional)
    :param age: Возраст (Optional)
    :param occupation_label: Код профессии (Optional)
    :param top_k: Количество похожих пользователей для поиска
    :param top_n: Количество рекомендаций
    :param exclude_seen: Исключать ли уже оценённые фильмы
    :param use_ratings_dataset: Использовать оценки из ratings.csv (True) или UserRating (False)
    :return: List of dicts with movie_id, predicted_rating, recommendation_score
    """
    # Формируем целевой профиль
    target_profile = {
        "gender": gender,
        "age": age,
        "occupation_label": occupation_label
    }
    
    # Находим похожих пользователей
    similar_users = find_similar_users(db, target_profile, top_k)
    
    if not similar_users:
        return []
    
    # Агрегируем: для каждого фильма считаем средневзвешенную оценку
    movie_scores = {}  # movie_id -> {"weighted_sum": float, "sim_sum": float}
    
    for user, sim in similar_users:
        # Загружаем оценки пользователя
        if use_ratings_dataset:
            # Используем оценки из ratings.csv
            ratings = db.query(Rating).filter(Rating.user_id == user.user_id).all()
        else:
            # Используем оценки из UserRating (новые пользователи)
            ratings = db.query(UserRating).filter(UserRating.user_id == user.user_id).all()
        
        for rating in ratings:
            movie_id = rating.movie_id
            
            if movie_id not in movie_scores:
                movie_scores[movie_id] = {"weighted_sum": 0, "sim_sum": 0}
            
            movie_scores[movie_id]["weighted_sum"] += rating.user_rating * sim
            movie_scores[movie_id]["sim_sum"] += sim
    
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
        
        result.append({
            "movie_id": movie.movie_id,
            "title": movie.movie_title,
            "movie_title": movie.movie_title,  # Алиас для совместимости
            "poster_url": movie.poster_url,
            "predicted_rating": rec["predicted_rating"]
        })
    
    return result


def get_recommendations_by_registered_user_profile(
    db: Session,
    user_id: int,
    top_k: int = 10,
    top_n: int = 20
) -> List[Dict[str, Any]]:
    """
    Возвращает рекомендации для зарегистрированного пользователя на основе его профиля.
    
    :param user_id: ID пользователя в RegisteredUser
    :param top_k: Количество похожих пользователей для поиска
    :param top_n: Количество рекомендаций
    :return: List of dicts with movie_id, title, predicted_rating
    """
    # Получаем профиль пользователя
    registered_user = db.query(RegisteredUser).filter(RegisteredUser.id == user_id).first()
    if not registered_user:
        return []
    
    # Конвертируем пол в булево
    gender_bool = None
    if registered_user.gender and registered_user.gender.lower() == "male":
        gender_bool = True
    elif registered_user.gender and registered_user.gender.lower() == "female":
        gender_bool = False
    
    # Получаем рекомендации
    recommendations = get_recommendations_by_profile(
        db=db,
        gender=gender_bool,
        age=registered_user.age,
        occupation_label=None,  # Для RegisteredUser не используем occupation_label напрямую
        top_k=top_k,
        top_n=top_n,
        use_ratings_dataset=True  # Используем оценки из ratings.csv
    )
    
    return recommendations
