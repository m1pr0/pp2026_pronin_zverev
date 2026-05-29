from passlib.context import CryptContext

# Используем pbkdf2_sha256 вместо bcrypt
# - Не требует внешних C-библиотек
# - Нет ограничения на длину пароля
# - Криптостойкий стандарт
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=310000  # Рекомендуемое количество раундов для 2024
)

def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием pbkdf2_sha256.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет пароль с использованием pbkdf2_sha256.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Если хеш не распознан (старый формат bcrypt) — возвращаем False
        return False