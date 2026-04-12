"""
security.py — Utilidades de seguridad: bcrypt y JWT.

Sprint 2: Reemplaza autenticación en texto plano por:
  - Hashing de contraseñas con bcrypt
  - Tokens JWT firmados con HS256 (python-jose)

Uso:
  - hash_password(plain)          → str  (al registrar)
  - verify_password(plain, hash)  → bool (al hacer login)
  - create_access_token(data)     → str  (al login exitoso)
  - get_current_user_email(token) → str  (en endpoints protegidos)
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import bcrypt

# ── Configuración ────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "planificador-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

bearer_scheme = HTTPBearer()


# ── Contraseñas ──────────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash bcrypt."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """
    Genera un token JWT firmado con los datos del usuario.

    Args:
        data (dict): Payload del token (ej: {"sub": email}).

    Returns:
        str: Token JWT firmado.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str:
    """
    Dependencia FastAPI — extrae y valida el email del token JWT.

    Usado en endpoints protegidos como:
        email = Depends(get_current_user_email)

    Raises:
        HTTPException 401: Si el token es inválido o expiró.
    """
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")