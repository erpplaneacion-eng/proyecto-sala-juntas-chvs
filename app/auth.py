"""
Módulo de autenticación del panel de administrador.
- Hash de contraseñas con bcrypt (passlib)
- Firma/verificación de cookies de sesión con itsdangerous
- Dependencia FastAPI get_current_admin()
"""
import os
from fastapi import Cookie, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext

# ----- Hash de contraseñas -----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ----- Sesión firmada (cookie) -----
def _get_serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SECRET_KEY", "chvs-insecure-default-key-change-me")
    return URLSafeTimedSerializer(secret, salt="admin-session")


def create_session_token(username: str) -> str:
    return _get_serializer().dumps(username)


def verify_session_token(token: str, max_age_seconds: int = 8 * 3600) -> str:
    """Devuelve el username si el token es válido, lanza excepción si no."""
    return _get_serializer().loads(token, max_age=max_age_seconds)


# ----- Dependencia FastAPI -----
def get_current_admin(admin_session: str | None = Cookie(default=None)) -> str:
    """
    Dependencia que verifica la cookie de sesión del admin.
    Si no es válida redirige al login.
    """
    if not admin_session:
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})
    try:
        username = verify_session_token(admin_session)
        return username
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})
