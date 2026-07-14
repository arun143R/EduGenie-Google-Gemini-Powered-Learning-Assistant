# pyrefly: ignore [missing-import]
import jwt
import bcrypt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, APIRouter, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models, schemas

# Absolute path to base directory to resolve templates robustly on Render
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Use standard OAuth2 password scheme for API-based login (docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

# Router for Authentication API
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed value.
    """
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a signed JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Store token expiry as UTC epoch timestamp
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user_from_token(token: str, db: Session) -> Optional[models.User]:
    """
    Helper function to validate token and return User model instance.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except jwt.PyJWTError:
        return None
        
    user = db.query(models.User).filter(models.User.username == username).first()
    return user

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency to retrieve the currently logged-in user.
    Checks HTTP cookies first (for web views) and then fallback to Authorization header.
    Throws a 401 Unauthorized if not authenticated.
    """
    # 1. Check HTTP-only cookie 'access_token' (format: Bearer <token> or just <token>)
    cookie_token = request.cookies.get("access_token")
    actual_token = None

    if cookie_token:
        if cookie_token.startswith("Bearer "):
            actual_token = cookie_token.split(" ")[1]
        else:
            actual_token = cookie_token
    elif token:
        actual_token = token

    if not actual_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_current_user_from_token(actual_token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    FastAPI dependency to retrieve the logged-in user if they exist, otherwise returns None.
    Does not throw exceptions if user is not authenticated.
    """
    cookie_token = request.cookies.get("access_token")
    actual_token = None

    if cookie_token:
        if cookie_token.startswith("Bearer "):
            actual_token = cookie_token.split(" ")[1]
        else:
            actual_token = cookie_token
    elif token:
        actual_token = token

    if not actual_token:
        return None

    return get_current_user_from_token(actual_token, db)


# --- Authentication Routes ---

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user in the database.
    Checks for existing username or email, hashes the password, and saves the new User.
    """
    # Check for duplicate username or email
    existing_user = db.query(models.User).filter(
        (models.User.username == payload.username) | 
        (models.User.email == payload.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered. Please use different credentials or log in."
        )

    # Hash password and create record
    hashed = get_password_hash(payload.password)
    new_user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
async def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user, generate JWT Access Token, set cookie, and return token data.
    """
    user = db.query(models.User).filter(
        (models.User.username == form_data.username) | 
        (models.User.email == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token
    access_token = create_access_token(data={"sub": user.username})

    # Set HTTP-only Cookie for seamless template requests
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=not settings.DEBUG
    )

    return schemas.Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout_user(response: Response):
    """
    Log out the user by deleting their access_token cookie.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully."}


# --- HTML View & Direct Auth Routes ---

html_router = APIRouter(tags=["Authentication HTML Views"])

@html_router.get("/login", response_class=HTMLResponse)
async def read_login(request: Request, user: Optional[models.User] = Depends(get_current_user_optional)):
    """
    Login view page. Redirects to dashboard if already authenticated.
    """
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html")

@html_router.post("/login", response_model=schemas.Token)
async def login_user_direct(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Direct login endpoint supporting standard form/JSON authentication.
    """
    return await login_user(response, form_data, db)

@html_router.get("/register", response_class=HTMLResponse)
async def read_register(request: Request, user: Optional[models.User] = Depends(get_current_user_optional)):
    """
    Register view page. Redirects to dashboard if already authenticated.
    """
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "register.html")

@html_router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user_direct(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Direct registration endpoint.
    """
    return await register_user(payload, db)

@html_router.get("/logout")
async def logout_user_get(response: Response):
    """
    Logout view endpoint. Clears auth cookie and redirects to login.
    """
    response.delete_cookie(key="access_token")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@html_router.post("/logout")
async def logout_user_post(response: Response):
    """
    Direct logout POST route.
    """
    return await logout_user(response)
