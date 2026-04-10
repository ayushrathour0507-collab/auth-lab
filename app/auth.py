from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from jose import jwt
from passlib.context import CryptContext
from .database import get_db
from . import models, schemas, dependencies
from .config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
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
def login(user_credentials: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    refresh_token_str = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = models.RefreshToken(
        token=refresh_token_str,
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

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(dependencies.get_current_user)):
    return current_user

@router.post("/logout")
def logout(request: schemas.RefreshTokenRequest, db: Session = Depends(get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == request.refresh_token).first()
    if db_token:
        db.delete(db_token)
        db.commit()
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=schemas.Token)
def refresh(request: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token == request.refresh_token).first()
    
    if not db_token or db_token.expires_at < datetime.utcnow():
        if db_token:
            db.delete(db_token)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    user_id = db_token.user_id
    db.delete(db_token)
    
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token_str = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_refresh_token = models.RefreshToken(
        token=refresh_token_str,
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
