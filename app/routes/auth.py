"""
routes/auth.py — Endpoints de autenticación.

Sprint 2: Login con bcrypt + JWT.
  POST /auth/login  → verifica bcrypt, retorna JWT
  GET  /auth/me     → retorna datos del usuario autenticado
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from .. import crud
from ..security import verify_password, create_access_token, get_current_user_email

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica al usuario con bcrypt y retorna un JWT.

    Returns:
        dict: { access_token, token_type, user_id, email, first_name, last_name }
    """
    user = crud.get_user_by_email(db, data.email)

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@router.get("/me")
def me(email: str = Depends(get_current_user_email), db: Session = Depends(get_db)):
    """
    Retorna los datos del usuario autenticado (valida el JWT).
    Usado por el frontend para verificar sesión activa.
    """
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "user_id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }