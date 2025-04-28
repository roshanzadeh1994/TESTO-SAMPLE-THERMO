from fastapi import APIRouter, Form, HTTPException, Depends, Request
from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import JSONResponse, HTMLResponse
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import openai
import os
import tempfile
import base64
from dotenv import load_dotenv
from db.database import get_db
from sqlalchemy.orm import Session
from db.db_device import create_device_inspection

# Initialize FastAPI app
app = FastAPI()

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Create API Router
router = APIRouter(tags=["router_AI"])

# Endpoint to process uploaded form file
@router.post("/process_form")
async def process_form(file: UploadFile = File(...)):
    """Extract form fields from uploaded file using OCR and AI."""
    try:
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}")
        temp_file.write(await file.read())
        temp_file_path = temp_file.name
        temp_file.close()

        # If PDF, convert to images
        if file.filename.endswith(".pdf"):
            images = convert_from_bytes(open(temp_file_path, "rb").read())
            extracted_text = "\n".join([pytesseract.image_to_string(img) for img in images])
        else:
            extracted_text = pytesseract.image_to_string(Image.open(temp_file_path))

        os.remove(temp_file_path)  # Clean up temp file

        # Use OpenAI to extract form fields
        openai_response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Extract all user-interactive form fields..."},
                {"role": "user", "content": extracted_text}
            ]
        )

        form_fields = openai_response['choices'][0]['message']['content']
        print("Extracted text:", extracted_text[:500])
        print("OpenAI response:", form_fields)

        return JSONResponse(content={"extracted_fields": form_fields})

    except Exception as e:
        print("Error in /process_form:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Endpoint to process voice input and fill form
@router.post("/process_voice")
async def process_voice(audio_base64: str = Body(...), extracted_fields: str = Body(...)):
    """Transcribe audio and match it with form fields."""
    try:
        # Decode Base64 audio
        audio_data = base64.b64decode(audio_base64)

        # Save audio temporarily
        temp_audio_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        with open(temp_audio_file_path, "wb") as audio_file:
            audio_file.write(audio_data)

        # Transcribe voice to text
        with open(temp_audio_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(model="whisper-1", file=audio_file)

        os.remove(temp_audio_file_path)  # Clean up temp file
        user_text = response['text']

        # Match transcribed text to form fields
        openai_response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": f"Using only the field names extracted from the form: {extracted_fields}..."},
                {"role": "user", "content": user_text}
            ]
        )

        filled_form = openai_response['choices'][0]['message']['content']

        return JSONResponse(content={"filled_form": filled_form})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Serve record.html file for /all (GET)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@router.get("/all", response_class=HTMLResponse)
async def get_record_voice():
    """Serve the HTML page to upload and record."""
    file_path = os.path.join(BASE_DIR, "..", "templates", "all.html")
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Serve record.html file for /all (POST)
@router.post("/all", response_class=HTMLResponse)
async def get_record_voice():
    """Serve the HTML page after form submission."""
    file_path = os.path.join(BASE_DIR, "..", "templates", "all.html")
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Save inspection data to database
@router.post("/api/save_inspection")
async def save_inspection(data: dict = Body(...), user_id: int = Body(...), db: Session = Depends(get_db)):
    """Save extracted and processed data into database."""
    try:
        inspection_data = {
            "data": data,
            "user_id": user_id
        }
        inspection = create_device_inspection(db, inspection_data)
        return {"message": "Inspection saved", "id": inspection.id}
    except Exception as e:
        return {"error": str(e)}
