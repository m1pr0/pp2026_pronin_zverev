from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from back.database import Base


class Movie(Base):
    __tablename__ = "movies"

    movie_id = Column(Integer, primary_key=True)
    movie_title = Column(Text, nullable=False)
    movie_genres = Column(Text)  # Строка кодов жанров через запятую: "0, 7"
    poster_url = Column(Text)

    # Связь с оценками
    ratings = relationship("Rating", back_populates="movie")

    def __repr__(self):
        return f"<Movie(id={self.movie_id}, title='{self.movie_title[:30]}...')>"


class User(Base):
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


class Rating(Base):
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
