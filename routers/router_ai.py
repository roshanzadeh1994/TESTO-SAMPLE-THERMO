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

app = FastAPI()

# Load API key securely
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Tesseract OCR path (adjust for your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
router = APIRouter(tags=["router_AI"])


@router.post("/process_form")
async def process_form(file: UploadFile = File(...)):
    """Process form from uploaded file."""
    try:
        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}")
        temp_file.write(await file.read())
        temp_file_path = temp_file.name
        temp_file.close()

        # Convert PDF to image if needed
        if file.filename.endswith(".pdf"):
            images = convert_from_bytes(open(temp_file_path, "rb").read())
            extracted_text = "\n".join([pytesseract.image_to_string(img) for img in images])
        else:
            extracted_text = pytesseract.image_to_string(Image.open(temp_file_path))

        os.remove(temp_file_path)  # Clean up temp file

        # AI extracts form fields
        openai_response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Extract all user-interactive form fields, including text inputs, dropdowns (single selection), checkboxes, and binary options (e.g., Yes/No, Ein oder Aus). Preserve the form’s structure and allowed selections while removing headers, instructions, buttons, and irrelevant content. Return the extracted fields in JSON format, exactly as they appear in the form."},
                {"role": "user", "content": extracted_text}
            ]
        )

        form_fields = openai_response['choices'][0]['message']['content']
        return JSONResponse(content={"extracted_fields": form_fields})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})





@router.post("/process_voice")
async def process_voice(audio_base64: str = Body(...), extracted_fields: str = Body(...)):
    """Process recorded voice input (Base64) and auto-fill the form."""
    try:
        # Decode Base64 audio
        audio_data = base64.b64decode(audio_base64)

        # Save to temp file
        temp_audio_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        with open(temp_audio_file_path, "wb") as audio_file:
            audio_file.write(audio_data)

        # Transcribe voice to text
        with open(temp_audio_file_path, "rb") as audio_file:
            response = openai.Audio.transcribe(model="whisper-1", file=audio_file)
        
        os.remove(temp_audio_file_path)  # Delete temp file
        user_text = response['text']

        # AI matches transcribed text with extracted fields
        openai_response = openai.ChatCompletion.create(
    model="gpt-4-turbo",
    messages=[
        {
            "role": "system",
            "content": f"""Using only the field names extracted from the form: {extracted_fields}, 
            fill in the fields with values from the transcribed text. Ensure that all fields are included. 
            If a field is missing or not mentioned in the voice input, assign a default value like 'Unknown', 'Not provided', or 0 for numbers. 
            
            Clearly differentiate values based on their source:
            - If the value comes from the extracted form, format it as "<span style='color: red;'>[Extracted] value</span>".  
            - If the value is from the voice input, format it as "<span style='color: green;'>[Voice] value</span>".  
            
            Ignore any additional information not related to these fields. 
            Return the result in structured JSON format, strictly adhering to these fields only."""
        },
        {"role": "user", "content": user_text}
    ]
)


        filled_form = openai_response['choices'][0]['message']['content']
        
        return JSONResponse(content={"filled_form": filled_form})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Serve HTML files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@router.get("/all", response_class=HTMLResponse)
async def get_record_voice():
    """Serve record.html"""
    file_path = os.path.join(BASE_DIR, "..", "templates", "all.html")


    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

