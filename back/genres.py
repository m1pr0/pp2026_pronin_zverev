# Стандартная кодировка жанров MovieLens
GENRE_MAPPING = {
    0: "Action",
    1: "Adventure",
    2: "Animation",
    3: "Children's",
    4: "Comedy",
    5: "Crime",
    6: "Documentary",
    7: "Drama",
    8: "Fantasy",
    9: "Film-Noir",
    10: "Horror",
    11: "Musical",
    12: "Mystery",
    13: "Romance",
    14: "Sci-Fi",
    15: "Thriller",
    16: "War",
    17: "Western",
}

# Обратный маппинг (название → код)
GENRE_REVERSE = {v: k for k, v in GENRE_MAPPING.items()}


def decode_genres(genre_codes_str: str) -> list[str]:
    """Декодирует строку кодов жанров в список названий."""
    if not genre_codes_str:
        return []
    
    try:
        codes = [int(x.strip()) for x in genre_codes_str.split(",")]
        return [GENRE_MAPPING.get(code, f"Unknown({code})") for code in codes]
    except (ValueError, AttributeError):
        return []


def encode_genres(genre_names: list[str]) -> list[int]:
    """Кодирует список названий жанров в коды."""
    return [GENRE_REVERSE.get(name, -1) for name in genre_names if name in GENRE_REVERSE]


def get_all_genres() -> dict[int, str]:
    """Возвращает полный словарь жанров {код: название}."""
    return GENRE_MAPPING.copy()
