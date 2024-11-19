from fastapi.security import OAuth2PasswordBearer  # Import für die Bearer-Token-Authentifizierung in FastAPI
from typing import Optional  # Import für optionale Typen
from datetime import datetime, timedelta  # Import von Datums- und Zeitfunktionen
from fastapi import Depends, status, HTTPException  # Import für Abhängigkeiten, HTTP-Statuscodes und Ausnahmen
from sqlalchemy.orm import Session  # Import für Datenbank-Sitzungen
from db.database import get_db  # Import der Funktion, um auf die Datenbank zuzugreifen
from fastapi.exceptions import HTTPException  # Import der HTTPException-Klasse für Fehlerbehandlung
from jose.exceptions import JWTError  # Import für Fehler beim JWT (JSON Web Token)
from db.db_user import get_user_by_username  # Import der Funktion zum Abrufen von Benutzerdaten nach Benutzernamen
import schemas  # Import von Schemata, die zur Datenvalidierung verwendet werden
from jose import JWTError, jwt  # Import von JWT für die Erstellung und Verifizierung von Tokens
from typing import Optional  # Doppelt importiert, könnte entfernt werden
from db import models  # Import der Datenbankmodelle

# OAuth2PasswordBearer ist ein klassischer Flow für die Authentifizierung mit Bearer-Token. "tokenUrl" ist die URL, an der Benutzer ein Token erhalten.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Konstanten für die JWT-Erstellung
SECRET_KEY = "b02e44cfa3c9d295b9ed2bc1b008359fcdbedefb22630b4f5f360906d29d85b7"  # Schlüssel, der zur Signierung des JWT verwendet wird
ALGORITHM = "HS256"  # Der Algorithmus zur Verschlüsselung des Tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Dauer, wie lange ein Token gültig ist (in Minuten)

# Funktion zur Erstellung eines JWTs
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Erstellt ein JWT-Access-Token.

    Parameter:
    - data (dict): Ein Dictionary, das die Nutzdaten des Tokens enthält.
    - expires_delta (Optional[timedelta]): Eine optionale Zeitspanne, bis wann der Token abläuft.

    Rückgabewert:
    - Das JWT als verschlüsselter String.
    """
    to_encode = data.copy()  # Kopiert die Daten, um sie zu kodieren
    if expires_delta:  # Wenn eine Ablaufzeit definiert ist
        expire = datetime.utcnow() + expires_delta  # Setzt das Ablaufdatum
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Standardmäßig auf 15 Minuten gesetzt
    to_encode.update({"exp": expire})  # Fügt die Ablaufzeit den zu kodierenden Daten hinzu
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Kodiert das JWT mit dem Secret Key und dem Algorithmus
    return encode_jwt  # Gibt das erstellte JWT zurück

# Funktion zur Verifizierung eines Tokens
def verify_token(token: str, credentials_exception):
    """
    Verifiziert ein übergebenes JWT.

    Parameter:
    - token (str): Der zu verifizierende Token.
    - credentials_exception: Die Ausnahme, die ausgelöst wird, wenn die Verifizierung fehlschlägt.

    Rückgabewert:
    - token_data: Die extrahierten Daten aus dem verifizierten Token.
    """
    try:
        # Dekodiert das JWT und überprüft die Signatur
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # Extrahiert den Benutzernamen aus dem Payload
        if username is None:  # Wenn der Benutzername nicht vorhanden ist
            raise credentials_exception
        token_data = schemas.TokenData(username=username)  # Erstellt ein TokenData-Schema
    except JWTError:  # Fehlerbehandlung bei JWT-Fehlern
        raise credentials_exception  # Wirft eine Ausnahme, wenn der Token ungültig ist
    return token_data  # Gibt die Token-Daten zurück

# Funktion, um den aktuell angemeldeten Benutzer anhand des Tokens abzurufen
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Holt den aktuell angemeldeten Benutzer basierend auf dem übergebenen JWT.

    Parameter:
    - token (str): Das JWT, das vom Benutzer übergeben wird.
    - db (Session): Die Datenbank-Sitzung, um auf die Benutzerdaten zuzugreifen.

    Rückgabewert:
    - user: Der aktuelle Benutzer, der aus der Datenbank abgerufen wird.
    """
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials")  # Ausnahme, wenn die Anmeldeinformationen ungültig sind
    try:
        # Dekodiert das Token und extrahiert den Benutzernamen
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # Extrahiert den Benutzernamen aus dem Payload
        if username is None:  # Wenn kein Benutzername im Token vorhanden ist
            raise credentials_exception
        token_data = schemas.TokenData(username=username)  # Erstellt ein TokenData-Schema
    except JWTError:
        raise credentials_exception  # Wirft eine Ausnahme, wenn der Token ungültig ist

    # Sucht den Benutzer in der Datenbank anhand des Benutzernamens
    user = db.query(models.DbUser).filter(models.DbUser.username == token_data.username).first()
    if user is None:  # Wenn der Benutzer nicht gefunden wird
        raise credentials_exception

    return user  # Gibt den Benutzer zurück
