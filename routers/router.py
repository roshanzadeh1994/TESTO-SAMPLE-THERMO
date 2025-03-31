import pandas as pd
from db.models import DeviceInspection
from db.db_device import create_device_inspection
import schemas
import tempfile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm.session import Session
from db import models
from db.database import get_db
from db.hash import Hash
from auth import oauth2
from fastapi import FastAPI, Request
from db.db_user import create_user
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi import Cookie

router = APIRouter(tags=["router"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=RedirectResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Verarbeitet den Benutzer-Login, prüft die Anmeldedaten und erstellt ein JWT-Token. Bei Erfolg wird der Benutzer weitergeleitet und die Anmeldedaten in Cookies gespeichert.
    """
    form_data = await request.form()
    username = form_data.get('username')
    password = form_data.get('password')

    user = db.query(models.DbUser).filter(models.DbUser.username == username).first()
    if not user or not Hash.verify(user.password, password):
        return templates.TemplateResponse("invalidUserPassword.html",
                                          {"request": request, "error": "Invalid username or password"})

    access_token = oauth2.create_access_token(data={"sub": username})

    expires = datetime.utcnow() + timedelta(seconds=90000)
    expires_utc = expires.replace(tzinfo=timezone.utc)

    response = RedirectResponse(url="/all")
    response.set_cookie(key="user_id", value=str(user.id), expires=expires_utc)
    response.set_cookie(key="username", value=username, expires=expires_utc)
    return response


@router.get("/all", response_class=HTMLResponse)
async def index(request: Request, user_id: Optional[str] = Cookie(None), username: Optional[str] = Cookie(None)):
    # Retrieve user information from cookies
    if not user_id or not username:
        # Handle case when user information is not available
        return RedirectResponse(url="/login")
    # Use user information in your HTML template
    return templates.TemplateResponse("all.html", {"request": request, "user_id": user_id, "username": username})


@router.post("/all", response_class=HTMLResponse)
async def process_login_form(request: Request, user_id: Optional[str] = Cookie(None),
                             username: Optional[str] = Cookie(None)):
    """
    Zeigt nach erfolgreichem Login die Hauptseite an, basierend auf den Benutzerinformationen aus den Cookies.

    Parameter:
    - request (Request): Die HTTP-Anfrage.
    - user_id (str): Benutzer-ID aus dem Cookie.
    - username (str): Benutzername aus dem Cookie.

    Rückgabewert:
    - HTMLResponse: Rendert die "index.html"-Seite mit Benutzerinformationen.
    """
    return templates.TemplateResponse("all.html", {"request": request, "user_id": user_id, "username": username})




@router.get("/signup/", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup/submit", response_class=RedirectResponse)
def signup(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Überprüfe, ob der Benutzer bereits existiert
    existing_user = db.query(models.DbUser).filter(models.DbUser.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Benutzer erstellen
    user = create_user(db, schemas.UserBase(username=username, email=email, password=password))
    # return user
    return RedirectResponse(url="/login")


@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})


@router.post("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})


@router.get("/about/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/profile/", response_class=HTMLResponse)
async def homepage(request: Request, user_id: Optional[str] = Cookie(None), username: Optional[str] = Cookie(None)):
    return templates.TemplateResponse("profile.html", {"request": request, "user_id": user_id, "username": username})


