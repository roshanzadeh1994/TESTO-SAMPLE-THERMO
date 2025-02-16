from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException,Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
import openai
import os
import tempfile
from db.database import get_db
from db.models import DeviceInspection
from pydantic import BaseModel
from dotenv import load_dotenv
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import json
from fastapi import FastAPI, UploadFile, File, Form, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db.models import Base
from sqlalchemy import Column, Integer, JSON

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


router = APIRouter(tags=["dynamic_form_service"])
templates = Jinja2Templates(directory="templates")
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class FormData(BaseModel):
    form_fields: dict  # Baraye zakhire field-ha ke dynamic hastand

# def extract_data_from_ai_response(response_content: str, form_fields: dict) -> dict:
#     extracted_data = {}
#     for field in form_fields.keys():
#         for line in response_content.split("\n"):
#             if field.lower() in line.lower():
#                 extracted_data[field] = line.split(":")[1].strip()
#     return extracted_data

def extract_data_from_ai_response(response_content: str) -> dict:
    extracted_data = {}
    for line in response_content.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            extracted_data[key.strip()] = value.strip()
    return extracted_data

@router.get("/upload_form")
async def upload_form_page(request: Request):
    return templates.TemplateResponse("upload_form.html", {"request": request})

@router.post("/upload_form")
async def upload_form(request: Request, file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["jpg", "jpeg", "png", "pdf"]:
            raise HTTPException(status_code=400, detail="Invalid file format. Only JPG, PNG, and PDF are allowed.")
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}")
        temp_file.write(await file.read())
        temp_file_path = temp_file.name
        temp_file.close()

        if file_ext == "pdf":
            images = convert_from_bytes(open(temp_file_path, "rb").read())
            extracted_text = "\n".join([pytesseract.image_to_string(img) for img in images])
        else:
            extracted_text = pytesseract.image_to_string(Image.open(temp_file_path))
        
        os.remove(temp_file_path)
        
        # OpenAI GPT-4 zur Extraktion der Formularfelder nutzen
        openai_response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Extract only the field names from the document, without any additional information, descriptions, or values. Return only a list of field names in JSON format."},
                {"role": "user", "content": extracted_text}
            ]
        )

        form_fields = json.loads(openai_response['choices'][0]['message']['content'])
        
        return templates.TemplateResponse("voice_input.html", {"request": request, "extracted_text": form_fields})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/process_voice")
async def process_voice(request: Request, audioFile: UploadFile = File(...), extracted_text: str = Form(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            temp_audio_file.write(await audioFile.read())
            temp_audio_file_path = temp_audio_file.name

        with open(temp_audio_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )

        
        os.remove(temp_audio_file_path)
        user_text = response['text']
        print("Transkribierter Text aus der Spracheingabe:", user_text, flush=True)

        
        openai_response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": f"Only return information related to fields of the following extracted data: {extracted_text}. Provide the result in structured JSON format just fill form in English or German language., If a field is missing or unclear, assign a **default value** like 'Unknown', 'Not provided', or 0 for numbers."},
                {"role": "user", "content": user_text}
            ]
        )
        # OpenAI-Antwort drucken, um Fehler zu erkennen
        print("🔄 OpenAI Response (Rohformat):", openai_response, flush=True)
        response_content = openai_response['choices'][0]['message']['content'].strip()
        
        if response_content.startswith("```json"):
            
            response_content = response_content.replace("```json", "").replace("```", "").strip()
        
         # Falls die Antwort leer ist
        if not response_content:
            print("OpenAI hat eine leere Antwort zurückgegeben!", flush=True)
            raise HTTPException(status_code=500, detail="OpenAI returned an empty response.")
        
        
        
        try:
            form_data = json.loads(response_content)
            print("✅ Bereinigte Antwort von OpenAI (JSON-Format):", form_data, flush=True)
        except json.JSONDecodeError:
            print("❌ OpenAI Antwort ist kein gültiges JSON!", flush=True)
            raise HTTPException(status_code=500, detail="OpenAI response is not valid JSON. Response: " + response_content)

        return templates.TemplateResponse("dynamic_form.html", {"request": request, "data": form_data, "clean_response": form_data})

    except Exception as e:
        print("❌ Fehler in `process_voice`:", str(e), flush=True)
        raise HTTPException(status_code=500, detail=f"Error processing voice file: {str(e)}")


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
