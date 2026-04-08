"""
FastAPI приложение для рекомендательной системы фильмов.
Endpoints:
- GET /api/genres - список доступных жанров
- GET /api/recommend/genre - рекомендации по жанрам
- POST /api/recommend/profile - рекомендации по профилю пользователя
"""

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from back.database import get_db, engine
from back.models import Base
from back import genre_recommendation_service
from back import profile_recommendation_service
from back.genres import get_all_genres

# Создаём таблицы при запуске (если не существуют)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Movie Recommender API",
    description="Сервис рекомендаций фильмов на основе жанров и профиля пользователя",
    version="1.0.0"
)

# CORS middleware (разрешаем все источники для локальной разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздаём статику (фронтенд)
FRONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "front")
app.mount("/front", StaticFiles(directory=FRONT_DIR), name="front")

@app.get("/")
def root():
    """Корневой endpoint — перенаправляет на фронтенд."""
    return FileResponse(os.path.join(FRONT_DIR, "index.html"))


@app.get("/api/genres")
def get_genres():
    """
    Возвращает список доступных жанров.
    
    Формат ответа:
    {
        "genres": {
            "0": "Action",
            "1": "Adventure",
            ...
        }
    }
    """
    genres = get_all_genres()
    # Преобразуем ключи в строки для JSON
    genres_str = {str(k): v for k, v in genres.items()}
    return {"genres": genres_str}


@app.get("/api/recommend/genre")
def recommend_by_genre(
    genres: List[str] = Query(..., description="Список названий жанров (например: ['Action', 'Drama'])"),
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество фильмов"),
    sort_by: str = Query("rating", regex="^(rating|popularity)$", description="Сортировка: rating или popularity"),
    db: Session = Depends(get_db)
):
    """
    Возвращает фильмы по выбранным жанрам.
    
    Параметры:
    - **genres**: Список названий жанров (например: ["Action", "Drama"])
    - **limit**: Максимальное количество фильмов (1-100)
    - **sort_by**: Сортировка - "rating" (средний рейтинг) или "popularity" (количество оценок)
    
    Пример: GET /api/recommend/genre?genres=Action&genres=Drama&limit=10&sort_by=rating
    """
    movies = genre_recommendation_service.get_movies_by_genres(
        db=db,
        genre_names=genres,
        limit=limit,
        sort_by=sort_by
    )
    
    return {
        "genres_requested": genres,
        "sort_by": sort_by,
        "count": len(movies),
        "movies": movies
    }


@app.post("/api/recommend/profile")
def recommend_by_profile(
    request: profile_recommendation_service.ProfileRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Возвращает рекомендации на основе профиля пользователя.
    
    **Параметры запроса (JSON):**
    - **gender**: Пол (true = Male, false = Female)
    - **age**: Возраст (число)
    - **occupation_label**: Код профессии (0-21)
    - **top_k**: Количество похожих пользователей (по умолчанию 10)
    - **top_n**: Количество рекомендаций (по умолчанию 20)
    
    **Пример запроса:**
    ```json
    {
        "gender": true,
        "age": 25,
        "occupation_label": 14,
        "top_k": 10,
        "top_n": 20
    }
    ```
    """
    movies = profile_recommendation_service.get_recommendations_by_profile(
        db=db,
        gender=request.gender,
        age=request.age,
        occupation_label=request.occupation_label,
        top_k=request.top_k,
        top_n=request.top_n
    )
    
    return {
        "profile": {
            "gender": "Male" if request.gender else "Female",
            "age": request.age,
            "occupation_label": request.occupation_label
        },
        "similar_users_count": request.top_k,
        "recommendations_count": len(movies),
        "movies": movies
    }


@app.get("/api/health")
def health_check():
    """Проверка работоспособности API."""
    return {"status": "ok"}
