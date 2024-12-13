from fastapi import APIRouter, Form, Depends, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import openai
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
            {"role": "system", "content": "Extrahiere beliebige Attribute und Werte aus dem Text."},
            {"role": "user", "content": f"{userText}"}
        ]
    )
    ai_response = response['choices'][0]['message']['content']
    ai_data = extract_data_from_ai_response(ai_response)

    # Save to database
    device_inspection = DeviceInspection(data=ai_data, user_id=1)  # Beispielhaft User ID 1
    db.add(device_inspection)
    db.commit()
    db.refresh(device_inspection)

    return templates.TemplateResponse("dynamic_form.html", {"request": request, "data": ai_data})



@router.post("/submit_dynamic_form", response_class=HTMLResponse)
async def submit_dynamic_form(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    data = {key: form_data[key] for key in form_data.keys()}

    # Save to database
    device_inspection = DeviceInspection(data=data, user_id=1)  # Beispielhaft User ID 1
    db.add(device_inspection)
    db.commit()
    db.refresh(device_inspection)

    return templates.TemplateResponse("success.html", {"request": request, "data": data})


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
                {"role": "system", "content": "Extrahiere beliebige Attribute und Werte aus dem Text."},
                {"role": "user", "content": f"{userText}"}
            ]
        )

        ai_response = response['choices'][0]['message']['content']
        ai_data = extract_data_from_ai_response(ai_response)

        # Daten in die Datenbank speichern
        device_inspection = DeviceInspection(data=ai_data, user_id=1)  # Beispielhaft User ID 1
        db.add(device_inspection)
        db.commit()
        db.refresh(device_inspection)

        # Temporäre Datei löschen
        os.remove(temp_audio_file_path)

        return templates.TemplateResponse("dynamic_form.html", {"request": request, "data": ai_data})

    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})