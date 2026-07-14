import os
from typing import Optional
from fastapi import FastAPI, Depends, Request, status, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import engine, Base, get_db
from app import models, auth, qna, explanation, summary, quiz, learning, history

# --- CSRF Protection Middleware ---
class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Checks Origin/Referer headers on state-changing requests to mitigate CSRF.
    Allows same-origin requests and requests with no referer (e.g. direct API clients).
    """
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            host = request.headers.get("host", "")
            allowed = False
            if origin:
                if host in origin:
                    allowed = True
            elif referer:
                if host in referer:
                    allowed = True
            else:
                allowed = True
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "CSRF check failed: request did not originate from this server."}
                )
        return await call_next(request)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifecycle context manager.
    Can be used to pre-load ML models, start background schedulers, or connect to brokers.
    """
    # Startup logic: create database tables if they do not exist
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic

app = FastAPI(
    title="EduGenie",
    description="A production-quality educational web application.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CSRF protection middleware (checked after lifespan, applied to all routes)
app.add_middleware(CSRFMiddleware)

# Absolute path resolution for templates and static files to ensure deployment compatibility
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount Static Files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Configure Jinja2 HTML Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Register Sub-Routers
app.include_router(auth.router)
app.include_router(qna.router)
app.include_router(explanation.router)
app.include_router(summary.router)
app.include_router(quiz.router)
app.include_router(learning.router)
app.include_router(history.router)


# --- HTML Template View Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request, user: Optional[models.User] = Depends(auth.get_current_user_optional)):
    """
    Home page. Redirects logged-in users directly to dashboard.
    """
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "index.html")


@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request, user: Optional[models.User] = Depends(auth.get_current_user_optional)):
    """
    Login view. Redirects to dashboard if already authenticated.
    """
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html")


@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request, user: Optional[models.User] = Depends(auth.get_current_user_optional)):
    """
    Register view. Redirects to dashboard if already authenticated.
    """
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "register.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(
    request: Request,
    user: Optional[models.User] = Depends(auth.get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    User workspace dashboard. Requires authenticated user.
    """
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Fetch some basic counts for the user dashboard
    quiz_count = db.query(models.Quiz).filter(models.Quiz.user_id == user.id).count()
    roadmap_count = db.query(models.Roadmap).filter(models.Roadmap.user_id == user.id).count()
    history_count = db.query(models.History).filter(models.History.user_id == user.id).count()

    context = {
        "request": request,
        "user": user,
        "quiz_count": quiz_count,
        "roadmap_count": roadmap_count,
        "history_count": history_count
    }
    return templates.TemplateResponse(request, "dashboard.html", context)


@app.get("/history", response_class=HTMLResponse)
async def read_history(
    request: Request,
    user: Optional[models.User] = Depends(auth.get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    User history page. Lists all past questions, explanations, summaries, and actions.
    """
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    history_items = db.query(models.History).filter(
        models.History.user_id == user.id
    ).order_by(models.History.created_at.desc()).all()

    context = {
        "request": request,
        "user": user,
        "history_items": history_items
    }
    return templates.TemplateResponse(request, "history.html", context)


@app.get("/logout")
async def logout_and_redirect(response: Response):
    """
    Log out the user by deleting their access_token cookie and redirecting to the homepage.
    """
    response.delete_cookie(key="access_token")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Catch HTTPExceptions and redirect HTML page views to /login on 401 Unauthorized errors.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
