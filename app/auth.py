from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import hashlib
import time
from threading import Lock
from jose import jwt
from passlib.context import CryptContext
from .database import get_db
from . import models, schemas, dependencies
from .config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store = {}
_rate_limit_lock = Lock()

def _check_rate_limit(request: Request, scope: str) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{scope}:{client_ip}"
    now = time.time()
    with _rate_limit_lock:
        attempts = _rate_limit_store.get(key, [])
        attempts = [stamp for stamp in attempts if now - stamp < RATE_LIMIT_WINDOW_SECONDS]
        if len(attempts) >= RATE_LIMIT_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )
        attempts.append(now)
        _rate_limit_store[key] = attempts

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def _create_token_pair(user: models.User, db: Session) -> dict:
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token_str = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = models.RefreshToken(
        token=hash_refresh_token(refresh_token_str),
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    _check_rate_limit(request, "register")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(request: Request, user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    _check_rate_limit(request, "login")
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return _create_token_pair(user, db)

@router.post("/token", response_model=schemas.Token)
def login_oauth2(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    _check_rate_limit(request, "token")
    # OAuth2 form sends `username`; we use email as the username field.
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return _create_token_pair(user, db)

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(dependencies.get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user

@router.post("/logout", response_model=schemas.MessageResponse)
def logout(request: schemas.RefreshTokenRequest, db: Session = Depends(get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == hash_refresh_token(request.refresh_token)
    ).first()
    if not db_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found")
    if db_token.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token does not belong to current user")
    db.delete(db_token)
    db.commit()
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=schemas.Token)
def refresh(
    req: Request,
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    _check_rate_limit(req, "refresh")
    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == hash_refresh_token(request.refresh_token)
    ).first()
    
    if not db_token or db_token.expires_at < datetime.utcnow():
        if db_token:
            db.delete(db_token)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    if not user or not user.is_active:
        db.delete(db_token)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token user")

    user_id = db_token.user_id
    db.delete(db_token)
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token_str = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_refresh_token = models.RefreshToken(
        token=hash_refresh_token(refresh_token_str),
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(new_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer"
    }
