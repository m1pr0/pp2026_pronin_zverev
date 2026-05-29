from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from back.database import Base as DatabaseBase


class Movie(DatabaseBase):
    __tablename__ = "movies"

    movie_id = Column(Integer, primary_key=True)
    movie_title = Column(Text, nullable=False)
    movie_genres = Column(Text)  # Строка кодов жанров через запятую: "0, 7"
    poster_url = Column(Text)

    # Связь с оценками
    ratings = relationship("Rating", back_populates="movie")

    def __repr__(self):
        return f"<Movie(id={self.movie_id}, title='{self.movie_title[:30]}...')>"


class User(DatabaseBase):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    user_gender = Column(Boolean)
    bucketized_user_age = Column(Integer)
    user_occupation_label = Column(Integer)
    user_occupation_text = Column(Text)
    user_zip_code = Column(String(10))

    # Связь с оценками
    ratings = relationship("Rating", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.user_id}, age={self.bucketized_user_age}, occupation='{self.user_occupation_text}')>"


class Rating(DatabaseBase):
    __tablename__ = "ratings"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.movie_id"), primary_key=True)
    user_rating = Column(Float)
    timestamp = Column(Integer)

    # Связи
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

    def __repr__(self):
        return f"<Rating(user={self.user_id}, movie={self.movie_id}, rating={self.user_rating})>"

# Новые модели для зарегистрированных пользователей и их оценок
class RegisteredUser(DatabaseBase):
    __tablename__ = "registered_users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    gender = Column(String, nullable=True, default=None)
    age = Column(Integer, nullable=True, default=None)
    profession = Column(String, nullable=True, default=None)

    # Связь с оценками пользователя
    user_ratings = relationship("UserRating", back_populates="registered_user")

class UserRating(DatabaseBase):
    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("registered_users.id"))
    movie_id = Column(Integer)
    rating = Column(Integer)
    created_at = Column(DateTime, default="now()")

    # Связь с зарегистрированным пользователем
    registered_user = relationship("RegisteredUser", back_populates="user_ratings")

