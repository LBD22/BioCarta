from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt as bcrypt_lib
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from ..models.user import User
from ..core.db import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt_lib.hashpw(password_bytes, bcrypt_lib.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    # bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt_lib.checkpw(password_bytes, hashed.encode('utf-8'))

def create_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expires_min)
    to_encode = {"sub": sub, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_alg)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise credentials_exception
    return user
