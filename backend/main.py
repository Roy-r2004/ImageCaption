from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
import os, shutil, uuid, base64, requests, re

from .captioning import generate_caption
from .titelling import generate_title
from .models import models
from .models.database import SessionLocal, engine, Base

# =========================
# 🔧 Config & Setup
# =========================

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or "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"
QWEN_MODEL = "qwen/qwen2.5-vl-72b-instruct:free"
QWEN_API_URL = "https://openrouter.ai/api/v1/chat/completions"

PROMPT_QWEN = """This is a product image. Analyze it carefully and respond ONLY in the following format:

Title: <short product name>
Tags: <comma-separated list of keywords>
Desc: <detailed and helpful product description>
Specs: <key specifications such as size, material, features, battery life, performance, etc. Use real product knowledge based on the image and search if needed>

Do NOT add anything else. Just respond in that exact format."""


# =========================
# 🧠 Utilities
# =========================

def extract_qwen_fields(text: str):
    pattern = r"Title:\s*(.*?)\nTags:\s*(.*?)\nDesc:\s*(.*?)\nSpecs:\s*(.*)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return None
    return {
        "title": match.group(1).strip(),
        "tags": match.group(2).strip(),
        "desc": match.group(3).strip(),
        "specs": match.group(4).strip(),
    }


def call_qwen_api(base64_image):
    body = {
        "model": QWEN_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_QWEN},
                    {"type": "image_url", "image_url": {"url": base64_image}}
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(QWEN_API_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# =========================
# 📦 Routes
# =========================

@app.get("/api/message")
def get_message():
    return {"message": "Hello from FastAPI!"}


@app.post("/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    model: str = Form("blip"),
    prompt: str = Form("Describe the image."),
    db: Session = Depends(get_db)
):
    try:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        caption = generate_caption(file_path, model_name=model, prompt=prompt)

        new_entry = models.ImageCaption(
            filename=filename,
            caption=caption,
            timestamp=datetime.utcnow()
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        return {
            "filename": filename,
            "caption": caption,
            "model": model,
            "prompt": prompt
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/api/generate-title")
async def generate_image_title(file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        title = generate_title(file_path)

        return {
            "filename": filename,
            "title": title
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/api/qwen-analyze")
async def analyze_product_qwen(file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(file_path, "rb") as image_file:
            image_data = image_file.read()
            mime = "jpeg" if ext in [".jpg", ".jpeg"] else ext.lstrip(".")
            base64_image = f"data:image/{mime};base64,{base64.b64encode(image_data).decode()}"

        result_text = call_qwen_api(base64_image)
        fields = extract_qwen_fields(result_text)

        return fields or {"error": "Failed to parse Qwen response."}

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    history = db.query(models.ImageCaption).order_by(models.ImageCaption.timestamp.desc()).all()
    return [
        {
            "filename": item.filename,
            "caption": item.caption,
            "timestamp": item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for item in history
    ]
