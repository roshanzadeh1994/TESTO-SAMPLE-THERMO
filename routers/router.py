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


@router.post("/login", response_class=RedirectResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Verarbeitet den Benutzer-Login, prüft die Anmeldedaten und erstellt ein JWT-Token. Bei Erfolg wird der Benutzer weitergeleitet und die Anmeldedaten in Cookies gespeichert.

    Ablauf:
    1. Überprüfung des Benutzernamens und Passworts.
    2. Bei Erfolg: Erstellen eines JWT-Tokens, Speichern der Daten in Cookies und Weiterleitung.
    3. Bei Fehler: Anzeige der Login-Seite mit Fehlermeldung.

    Rückgabewert:
    - RedirectResponse bei erfolgreichem Login.
    - HTMLResponse bei fehlerhafter Anmeldung.
    """
    form_data = await request.form()
    username = form_data.get('username')
    password = form_data.get('password')

    user = db.query(models.DbUser).filter(models.DbUser.username == username).first()
    if not user or not Hash.verify(user.password, password):
        # Render the login page with an error message
        return templates.TemplateResponse("invalidUserPassword.html",
                                          {"request": request, "error": "Invalid username or password"})

    access_token = oauth2.create_access_token(data={"sub": username})

    # Ablaufzeit für Cookies festlegen (z.B. 1 Stunde)
    expires = datetime.utcnow() + timedelta(seconds=90000)
    expires_utc = expires.replace(tzinfo=timezone.utc)  # Setze die Zeitzone auf UTC

    # Save user information in cookie with expiration time
    response = RedirectResponse(url="/login/formular")
    response.set_cookie(key="user_id", value=str(user.id), expires=expires_utc)
    response.set_cookie(key="username", value=username, expires=expires_utc)
    return response


@router.get("/login/formular", response_class=HTMLResponse)
async def index(request: Request, user_id: Optional[str] = Cookie(None), username: Optional[str] = Cookie(None)):
    # Retrieve user information from cookies
    if not user_id or not username:
        # Handle case when user information is not available
        return RedirectResponse(url="/login")
    # Use user information in your HTML template
    return templates.TemplateResponse("index.html", {"request": request, "user_id": user_id, "username": username})


@router.post("/login/formular", response_class=HTMLResponse)
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
    return templates.TemplateResponse("index.html", {"request": request, "user_id": user_id, "username": username})


@router.post("/login/formular/submit/", response_class=HTMLResponse)
async def submit_device_inspection(request: Request, db: Session = Depends(get_db),
                                 user_id: Optional[str] = Cookie(None)):
    """
        Verarbeitet das Inspektionsformular, erstellt einen neuen Eintrag und zeigt alle Inspektionen des Benutzers an.

        Parameter:
        - request (Request): Die HTTP-Anfrage mit Formulardaten.
        - db (Session): Datenbank-Sitzung für die Inspektionserstellung.
        - user_id (str): Benutzer-ID aus dem Cookie.

        Ablauf:
        1. Überprüft die Authentifizierung.
        2. Extrahiert die Formulardaten und erstellt einen neuen Inspektionseintrag.
        3. Zeigt alle Inspektionen des Benutzers an.

        Rückgabewert:
        - HTMLResponse: Zeigt die Seite mit allen Inspektionen.
        """
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

    form_data = await request.form()
    inspection_location = form_data.get("inspection_location")
    device_name = form_data.get("device_name")
    inspection_date = form_data.get("inspection_date")
    inspection_details = form_data.get("inspection_details")
    kältepump = int(form_data.get("kältepump"))

    # Convert date string to datetime object
    if inspection_date:
        inspection_date = datetime.strptime(inspection_date, "%Y-%m-%d").date()

    device_inspection = schemas.DeviceInspectionInput(
        inspection_location=inspection_location,
        device_name=device_name,
        inspection_date=inspection_date,
        inspection_details=inspection_details,
        kältepump=kältepump,
        user_id=int(user_id),  # Convert user_id to int
    )

    # Inspektion erstellen
    create_device_inspection(db, device_inspection.dict())

    # Alle Inspektionsinformationen abrufen
    all_inspections = db.query(DeviceInspection).filter_by(user_id=int(user_id)).all()

    # Vorlage für die Erfolgsseite mit allen Inspektionsinformationen und Download-Button rendern
    return templates.TemplateResponse("show_all_inspections.html", {"request": request, "inspections": all_inspections})


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


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


@router.get("/download/")
async def download_device_inspections(db: Session = Depends(get_db)):
    try:
        inspections = db.query(DeviceInspection).all()

        if not inspections:
            raise HTTPException(status_code=404, detail="No device inspections found")

        inspection_data = {
            "Inspection Location": [inspection.inspection_location for inspection in inspections],
            "device Name": [inspection.device_name for inspection in inspections],
            "Inspection Date": [inspection.inspection_date for inspection in inspections],
            "Inspection Details": [inspection.inspection_details for inspection in inspections],
            "Kältepump": [inspection.kältepump for inspection in inspections],
            "User_id": [inspection.user_id for inspection in inspections]

        }

        df = pd.DataFrame(inspection_data)

        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            filename = tmp_file.name

            # Schreibe den DataFrame in die temporäre Datei
            df.to_excel(tmp_file, index=False)

        # Gebe die temporäre Datei zurück
        return FileResponse(filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#
