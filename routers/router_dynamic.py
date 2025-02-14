from fastapi import APIRouter, Form, Depends, Request, UploadFile, File, HTTPException, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import openai
from datetime import datetime
from db.database import get_db
from db.models import DeviceInspection
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import tempfile

router = APIRouter(tags=["router_dynamic"])
templates = Jinja2Templates(directory="templates")

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")



class UserText(BaseModel):
    userText: str

def parse_date(date_str: str) -> str:
    """
    Diese Funktion versucht, einen Datumsstring in das Format 'YYYY-MM-DD' zu konvertieren.
    Sie unterstützt verschiedene Formate für numerische und sprachliche Datumsangaben, einschließlich deutscher und englischer Monatsnamen.

    Parameter:
    - date_str (str): Der Datumsstring, der geparst werden soll.

    Rückgabewert:
    - str: Das formatierte Datum im 'YYYY-MM-DD'-Format oder der Standardwert '1111-11-11', wenn das Datum nicht erkannt wird.
    """
    date_str = date_str.strip().lower()  # Entfernt Leerzeichen und konvertiert den Text in Kleinbuchstaben

    if not date_str or date_str == "nicht angegeben":  # Spezieller Fall für 'nicht angegeben'
        return "1111-11-11"

    # Unterstützte Datumsformate (numerisch, deutsch, englisch)
    date_formats = [
        '%d.%m.%Y', '%Y-%m-%d',  # Numerische Formate
        '%d. %B %Y', '%d. %b %Y',  # Deutsche Monatsnamen, lang und kurz
        '%d %B %Y', '%d %b %Y', '%B %d, %Y'  # Englische Monatsnamen, lang und kurz
    ]

    # Deutsche Monatsnamen durch englische Monatsnamen ersetzen
    german_to_english = {
        'januar': 'january', 'februar': 'february', 'märz': 'march', 'mai': 'may',
        'juni': 'june', 'juli': 'july', 'oktober': 'october', 'dezember': 'december',
        'apr.': 'apr', 'aug.': 'aug', 'dez.': 'dec'
    }

    # Ersetzen der deutschen Monatsnamen im Datum
    for german, english in german_to_english.items():
        date_str = date_str.replace(german, english)

    # Versuch, das Datum im angegebenen Format zu parsen
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format)
            return parsed_date.strftime('%Y-%m-%d')  # Gibt das Datum im 'YYYY-MM-DD'-Format zurück
        except ValueError:
            continue

    return "1111-11-11"  # Rückgabe eines Standardwerts, wenn das Parsen fehlschlägt


def extract_data_from_ai_response(response_content: str) -> dict:
    data = {}
    lines = response_content.strip().split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()
    return data


@router.get("/text_input", response_class=HTMLResponse)
async def text_input(request: Request):
    return templates.TemplateResponse("Text-input.html", {"request": request})


@router.post("/process_text", response_class=HTMLResponse)
async def process_text(request: Request, userText: str = Form(...), db: Session = Depends(get_db)):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Extrahiere beliebige Attribute und Werte aus dem Text(fill out in English language)."},
            {"role": "user", "content": f"{userText}"}
        ]
    )
    ai_response = response['choices'][0]['message']['content']

    ai_response_clean = ai_response.replace('-', '').replace(' - ', '').strip()
    print("Bereinigte Antwort von OpenAI:", ai_response_clean)

    ai_data = extract_data_from_ai_response(ai_response_clean)
    ai_data = {key.replace('-', '').strip(): value for key, value in ai_data.items()}

# Überprüfung auf das erforderliche Feld "First and Lastname"
    required_field = "First and Lastname" or "Firstname and Lastname"
    if required_field.lower not in ai_data or not ai_data[required_field]:
        warning_message = f"The field '{required_field}' is required. Please fill it out."
        return templates.TemplateResponse(
            "dynamic_form.html",
            {"request": request, "data": ai_data, "warning": warning_message}
        )

    return templates.TemplateResponse("dynamic_form.html", {"request": request, "data": ai_data, "clean_response": ai_response_clean})






@router.post("/submit_dynamic_form", response_class=HTMLResponse)
async def submit_dynamic_form(
    request: Request, 
    db: Session = Depends(get_db), 
    user_id: str = Cookie(None), 
    username: str = Cookie(None)
):
    # Prüfen, ob der Benutzer authentifiziert ist
    if not user_id or not username:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Formulardaten extrahieren
    form_data = await request.form()
    data = {key: form_data[key] for key in form_data.keys()}

    # Datenbankeintrag erstellen
    device_inspection = DeviceInspection(data=data, user_id=int(user_id))
    db.add(device_inspection)
    db.commit()
    db.refresh(device_inspection)

    inspections = [device_inspection]

    return templates.TemplateResponse("success.html", {"request": request, "inspections": inspections})



@router.get("/process_voice", response_class=HTMLResponse)
async def get_process_voice(request: Request):
    """
    Stellt eine HTML-Seite dar, die es dem Benutzer ermöglicht, eine Audioaufnahme zur Verarbeitung hochzuladen.

    Parameter:
    - request (Request): Die HTTP-Anfrage.

    Rückgabewert:
    - HTMLResponse: Gibt die "Text-input.html"-Seite zurück, auf der der Benutzer die Sprachaufnahme hochladen kann.
    """
    return templates.TemplateResponse("Text-input.html", {"request": request})


@router.post("/process_voice", response_class=HTMLResponse)
async def process_voice(request: Request, audioFile: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Speichert die hochgeladene Audiodatei temporär
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            temp_audio_file.write(await audioFile.read())
            temp_audio_file_path = temp_audio_file.name

        # Audiodatei mit OpenAI Whisper transkribieren
        with open(temp_audio_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )

        # Extrahierter Text aus der Audiodatei
        userText = response['text']

        # OpenAI API zur Datenauswertung verwenden
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Extrahiere beliebige Attribute und Werte aus dem Text(fill out in English language)."},
                {"role": "user", "content": f"{userText}"}
            ]
        )


        ai_response = response['choices'][0]['message']['content']

        ai_response_clean = ai_response.replace('-', '').replace(' - ', '').strip()
        print("Bereinigte Antwort von OpenAI:", ai_response_clean)

        ai_data = extract_data_from_ai_response(ai_response_clean)
        ai_data = {key.replace('-', '').strip(): value for key, value in ai_data.items()}



        # Temporäre Datei löschen
        os.remove(temp_audio_file_path)

        return templates.TemplateResponse("dynamic_form.html", {"request": request, "data": ai_data, "clean_response": ai_response_clean})

    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})