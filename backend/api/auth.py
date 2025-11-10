from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.security import get_db, hash_password, verify_password, create_token
from ..schemas.auth import RegisterIn, LoginIn, TokenOut
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password),
                language=payload.language, sex=payload.sex, birthdate=payload.birthdate)
    db.add(user); db.commit()
    token = create_token(sub=user.email)
    return TokenOut(access_token=token)

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(sub=user.email)
    return TokenOut(access_token=token)
