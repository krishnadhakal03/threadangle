import bcrypt
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import database
import models

JWT_SECRET = os.getenv("JWT_SECRET", "secret")
ALGORITHM = "HS256"
BETA_WAITLIST_MESSAGE = (
    "Thank you for signing up. Threadangle is currently in private beta testing. "
    "You have been added to our priority waitlist. Our admin will contact you shortly, "
    "and we will email you once Threadangle officially opens."
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def _truthy_env(name: str, default: str = "0") -> bool:
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def beta_waitlist_mode_enabled() -> bool:
    return _truthy_env("ENABLE_BETA_WAITLIST_MODE", "0")


def beta_full_access_emails() -> set[str]:
    raw = os.getenv("BETA_FULL_ACCESS_EMAILS", os.getenv("VIDEO_RENDER_ALLOWED_USER_EMAIL", "krishna.dhakal03@gmail.com"))
    return {email.strip().lower() for email in raw.split(",") if email.strip()}


def user_has_beta_full_access(user_or_email) -> bool:
    if not beta_waitlist_mode_enabled():
        return True
    email = user_or_email if isinstance(user_or_email, str) else getattr(user_or_email, "email", "")
    return str(email or "").strip().lower() in beta_full_access_emails()


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30) # As per guide
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def require_full_access_user(current_user: models.User = Depends(get_current_user)):
    if not user_has_beta_full_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=BETA_WAITLIST_MESSAGE)
    return current_user
