from fastapi import APIRouter, Depends, \
    status  # Importieren von Modulen für das Routing und die Abhängigkeiten in FastAPI
from fastapi.security.oauth2 import OAuth2PasswordRequestForm  # OAuth2-Authentifizierungsformular für Benutzeranfragen
from sqlalchemy.orm.session import Session  # Session-Klasse zur Verwaltung der Datenbank-Sitzung
from db import models  # Importieren der Datenbankmodelle aus dem Projekt
from db.database import get_db  # Funktion zur Bereitstellung der Datenbankverbindung
from fastapi.exceptions import HTTPException  # Ausnahmebehandlung für HTTP-spezifische Fehler
from db.hash import Hash  # Importieren von Funktionen zum Hashing und Verifizieren von Passwörtern
from auth import oauth2  # Importieren des Authentifizierungsmoduls für OAuth2

# Erstellen eines Routers für API-Endpunkte im Zusammenhang mit der Authentifizierung
router = APIRouter(tags=["authentication"])


# Definition eines POST-Endpunkts zum Abrufen eines Tokens für die Benutzeranmeldung
@router.post("/token")
def get_token(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Diese Funktion wird verwendet, um ein Zugangstoken für einen Benutzer zu generieren.

    Parameter:
    - request (OAuth2PasswordRequestForm): Enthält das Benutzeranmeldeformular mit dem Benutzernamen und Passwort.
    - db (Session): Eine Datenbanksitzung, die zur Abfrage der Benutzerdaten verwendet wird.

    Ablauf:
    1. Der Benutzername wird aus der Datenbank abgerufen.
    2. Wenn der Benutzer nicht existiert, wird eine HTTP 404-Fehlerausnahme ausgelöst.
    3. Das eingegebene Passwort wird mit dem in der Datenbank gespeicherten Passwort verglichen.
    4. Wenn das Passwort falsch ist, wird ebenfalls eine HTTP 404-Fehlerausnahme ausgelöst.
    5. Ein JWT (JSON Web Token) wird erstellt und an den Benutzer zurückgegeben.

    Rückgabewert:
    - Ein JSON-Objekt mit dem Zugangstoken, dem Token-Typ, der Benutzer-ID und dem Benutzernamen.
    """
    # Suche nach dem Benutzer in der Datenbank anhand des Benutzernamens
    user = db.query(models.DbUser).filter(models.DbUser.username == request.username).first()

    # Überprüfen, ob der Benutzer existiert
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid credentials")

    # Verifizieren des Passworts
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid password")

    # Erstellen eines Access-Tokens mit dem Benutzernamen als Payload
    access_token = oauth2.create_access_token(data={"sub": request.username})

    # Rückgabe des Access-Tokens und weiterer Benutzerdaten
    return {
        "access_token": access_token,
        "type_token": "bearer",  # Token-Typ wird auf "bearer" gesetzt
        "userID": user.id,  # Benutzer-ID
        "username": user.username  # Benutzername
    }
