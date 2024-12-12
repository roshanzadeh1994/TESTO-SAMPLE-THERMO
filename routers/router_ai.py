from fastapi import APIRouter, Form, HTTPException, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import openai
from pydantic import BaseModel
from db.database import get_db
from datetime import datetime
import os
import tempfile
from typing import Optional
import json
from datetime import datetime
from dotenv import load_dotenv

router = APIRouter(tags=["router_AI"])
templates = Jinja2Templates(directory="templates")

load_dotenv(dotenv_path="C:/Users/1000len-8171/Desktop/testo-sample-thermo/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")


class UserText(BaseModel):
    """
    Ein Pydantic-Modell, das den Text repräsentiert, den der Benutzer übermittelt.

    Attribute:
    - userText (str): Der vom Benutzer eingegebene Text.
    """
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
    """
    Extrahiert die relevanten Daten aus der Antwort einer KI und formatiert sie in einem Dictionary.

    Die Extraktion basiert auf Schlüsseln wie 'inspection location', 'device name', 'inspection date', 'inspection details', 'kältepump'.

    Parameter:
    - response_content (str): Der Text, der von der KI zurückgegeben wurde.

    Rückgabewert:
    - dict: Ein Dictionary mit den extrahierten Werten.
    """
    data = response_content.strip().split('\n')  # Zerlegt den Text in einzelne Zeilen
    ai_user_data = {}

    for item in data:
        key_value = item.split(':')  # Zerlegt jede Zeile in Schlüssel und Wert
        if len(key_value) == 2:
            key = key_value[0].strip().lower().replace('-', '').strip()  # Normalisiert den Schlüssel
            value = key_value[1].strip()

# Zuordnung der extrahierten Daten zu den richtigen Schlüsseln
            if 'ort' in key or 'location' in key or 'standort' in key or 'place' in key or 'city' in key:
                key = 'inspection location'
            if 'devicesname' in key or 'device' in key or 'device name' in key:
                key = 'device name'
            if 'datum' in key or 'date' in key:
                key = 'inspection date'
            if 'details' in key or 'beschreibung' in key or 'erklärung' in key:
                key = 'inspection details'
            if 'numerisch' in key or 'number' in key or 'wert' in key or 'kälte' in key or 'pump' in key or 'kältepump' in key:
                key = 'kältepump'

            ai_user_data[key] = value

    return ai_user_data  # Rückgabe des extrahierten Daten-Dictionary





@router.get("/text_input", response_class=HTMLResponse)
async def text_input(request: Request):
    return templates.TemplateResponse("Text-input.html", {"request": request})


@router.post("/process_text", response_class=HTMLResponse)
async def process_text(request: Request, userText: str = Form(...), db: Session = Depends(get_db)):
    """
    Diese Funktion verarbeitet den vom Benutzer eingegebenen Text, sendet ihn an die OpenAI-API und extrahiert die relevanten Daten.

    Parameter:
    - request (Request): Die HTTP-Anfrage mit den Benutzereingaben.
    - userText (str): Der Text, der vom Benutzer eingegeben wurde.
    - db (Session): Eine Datenbanksitzung, die verwendet wird, um auf die Datenbank zuzugreifen (abhängig von FastAPI).

    Ablauf:
    1. Sendet den vom Benutzer eingegebenen Text an das GPT-4-Modell und bittet um Extraktion der relevanten Daten (z.B. 'inspection location', 'device name', 'inspection date', 'inspection details', 'kältepump').
    2. Verarbeitet die Antwort der OpenAI-API und extrahiert die relevanten Daten in ein Dictionary.
    3. Überprüft, ob alle erforderlichen Daten extrahiert wurden. Falls Daten fehlen, fordert es den Benutzer auf, die fehlenden Informationen anzugeben.
    4. Wenn alle Daten vorhanden sind, wird die Antwort im Template "indexAI.html" dargestellt..

    Rückgabewert:
    - HTMLResponse: Stellt entweder die extrahierten Daten oder ein Template zur Ergänzung fehlender Informationen dar.

Fehlerbehandlung:
    - Bei einem Fehler bei der OpenAI-Anfrage oder der Verarbeitung wird ein HTTP-Fehlerstatus zurückgegeben.
    """
    try:
        # Anfrage an die OpenAI-API, um die relevanten Daten aus dem Text zu extrahieren
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                {"role": "user",
                "content": f"Extrahiere die relevanten Informationen aus dem Text {userText} basierend auf den folgenden Schlüsseln: 'inspection location', 'device name', 'inspection date', 'inspection details' und 'kältepump' Kältepump muss nur nummer sein"
                 }
            ],
         
        )



        print("Antwort von OpenAI:", response)

        # Überprüfung, ob eine gültige Antwort von OpenAI empfangen wurde
        if not response or 'choices' not in response or len(response['choices']) == 0:
            ai_response = None
        else:
            ai_response = response['choices'][0]['message'].get('content')

        default_values = {
            'inspection location': 'kein Ort wurde eingegeben',
            'device name': 'kein Name wurde eingegeben',
            'inspection date': '1111-11-11',
            'inspection details': 'keine Details verfügbar',
            'kältepump': 0
        }

        if not ai_response:
            ai_user_data = default_values
   
        else:
        # Entferne Markdown-Formatierung (** oder __)
            ai_response_clean = ai_response.replace('**', '').replace('__', '').strip()
            print("Bereinigte Antwort von OpenAI:", ai_response_clean)

        # Extrahiere die relevanten Daten aus der bereinigten Antwort
            ai_user_data = extract_data_from_ai_response(ai_response_clean)
            ai_user_data = {key.replace('**', '').strip(): value for key, value in ai_user_data.items()}

        # Überprüfen auf fehlende Daten und Standardwerte zuweisen

            for key, default in default_values.items():
                if key not in ai_user_data or not ai_user_data[key]:
                    ai_user_data[key] = default

        if 'kältepump' in ai_user_data:
            try:
                ai_user_data['kältepump'] = int(ai_user_data['kältepump'])
            except ValueError:
                ai_user_data['kältepump'] = 0

        if ai_user_data["inspection date"]:
            ai_user_data["inspection date"] = parse_date(ai_user_data['inspection date'])

        return templates.TemplateResponse("indexAI.html", {"request": request, "data": ai_user_data, "clean_response": ai_response_clean})

    except openai.error.OpenAIError as e:
        ai_user_data = {
            'inspection location': 'kein Ort wurde eingegeben',
            'device name': 'kein Name wurde eingegeben',
            'inspection date': '1111-11-11',
            'inspection details': 'keine Details verfügbar',
            'kältepump': 0
        }
        return templates.TemplateResponse("indexAI.html", {"request": request, "data": ai_user_data, "clean_response": ai_response_clean})

    except Exception as e:
        ai_user_data = {
            'inspection location': 'kein Ort wurde eingegeben',
            'device name': 'kein Name wurde eingegeben',
            'inspection date': '1111-11-11',
            'inspection details': 'keine Details verfügbar',
            'kältepump': 0
        }
        return templates.TemplateResponse("indexAI.html", {"request": request, "data": ai_user_data, "clean_response": ai_response_clean})

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
async def post_process_voice(request: Request, audioFile: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Diese Funktion verarbeitet eine hochgeladene Audiodatei, konvertiert sie in Text, extrahiert relevante Daten mithilfe der OpenAI-API und gibt diese in einer HTML-Antwort zurück.

    Parameter:
    - request (Request): Die HTTP-Anfrage mit der hochgeladenen Audiodatei.
    - audioFile (UploadFile): Die vom Benutzer hochgeladene Audiodatei.
    - db (Session): Eine Datenbanksitzung, die verwendet wird, um auf die Datenbank zuzugreifen.

    Ablauf:
    1. Die Audiodatei wird in einer temporären Datei gespeichert.
    2. Mithilfe des Whisper-Modells (OpenAI) wird die Audiodatei in Text umgewandelt.
    3. Der transkribierte Text wird an das GPT-4-Modell gesendet, um relevante Daten zu extrahieren, wie z.B. 'inspection location', 'device name', 'inspection date', 'inspection details', und 'kältepump'.
    4. Falls Daten fehlen, wird der Benutzer aufgefordert, diese zu ergänzen.
    5. Wenn alle erforderlichen Daten vorhanden sind, werden sie in einer HTML-Vorlage angezeigt.

    Rückgabewert:
    - HTMLResponse: Stellt entweder die extrahierten Daten oder eine Seite zur Ergänzung fehlender Informationen dar.

    Fehlerbehandlung:
    - Bei einem Fehler bei der Anfrage an die OpenAI-API oder der Verarbeitung wird ein HTTP-Fehlerstatus zurückgegeben.
    """
    try:
        # Speichert die Audiodatei temporär auf dem Server
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            temp_audio_file.write(await audioFile.read())
            temp_audio_file_path = temp_audio_file.name

        # Konvertiert die Audiodatei in Text mit OpenAI's Whisper-Modell
        with open(temp_audio_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )

        userText = response['text']  # Extrahierter Text aus der Audiodatei

        # Löscht die temporäre Audiodatei
        os.remove(temp_audio_file_path)

        # Anfrage an OpenAI, um die relevanten Daten aus dem Text zu extrahieren
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                {"role": "user",
                 "content": f"Extrahiere die relevanten Daten (location, device name, date, details, kältepump) aus diesem Text: {userText}"}
            ]
        )

        print("Antwort von OpenAI:", response)  # Debugging-Ausgabe

        if not response or 'choices' not in response or len(response['choices']) == 0:
            ai_response = None
        else:
            ai_response = response['choices'][0]['message'].get('content')

        default_values = {
            'inspection location': 'kein Ort wurde eingegeben',
            'device name': 'kein Name wurde eingegeben',
            'inspection date': '1111-11-11',
            'inspection details': 'keine Details verfügbar',
            'kältepump': 0
        }

        if not ai_response:
            ai_user_data = default_values
        else:
        # Entferne Markdown-Formatierung (** oder __)
            ai_response_clean = ai_response.replace('**', '').replace('__', '').strip()
            print("Bereinigte Antwort von OpenAI:", ai_response_clean)

        # Extrahiere die relevanten Daten aus der bereinigten Antwort
            ai_user_data = extract_data_from_ai_response(ai_response_clean)
            ai_user_data = {key.replace('**', '').strip(): value for key, value in ai_user_data.items()}

        # Überprüfen auf fehlende Daten und Standardwerte zuweisen

            for key, default in default_values.items():
                if key not in ai_user_data or not ai_user_data[key]:
                    ai_user_data[key] = default

        if 'kältepump' in ai_user_data:
            try:
                ai_user_data['kältepump'] = int(ai_user_data['kältepump'])
            except ValueError:
                ai_user_data['kältepump'] = 0

        if ai_user_data["inspection date"]:
            ai_user_data["inspection date"] = parse_date(ai_user_data['inspection date'])

        return templates.TemplateResponse("indexAI.html", {"request": request, "data": ai_user_data, "clean_response": ai_response_clean})

    except openai.error.OpenAIError as e:
        ai_user_data = {
            'inspection location': 'kein Ort wurde eingegeben',
            'device name': 'kein Name wurde eingegeben',
            'inspection date': '1111-11-11',
            'inspection details': 'keine Details verfügbar',
            'kältepump': 0
        }
        return templates.TemplateResponse("indexAI.html", {"request": request, "data": ai_user_data})

    except Exception as e:
        ai_user_data = {
            'inspection location': 'kein Ort wurde eingegeben',
            'device name': 'kein Name wurde eingegeben',
            'inspection date': '1111-11-11',
            'inspection details': 'keine Details verfügbar',
            'kältepump': 0
        }
        return templates.TemplateResponse("indexAI.html", {"request": request, "data": ai_user_data, "clean_response": ai_response_clean})


