from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os, shutil, uuid
from datetime import datetime

from .captioning import generate_caption
from .titelling import generate_title  # ✅ Import title generation
from .models import models
from .models.database import SessionLocal, engine, Base

# =========================
# 🔧 Initial Setup
# =========================

# Create DB tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Enable CORS for Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload folder setup
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# ✅ Routes
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
    print(f"🚀 Upload received: {file.filename}")
    print(f"🧠 Using model: {model} with prompt: {prompt}")

    try:
        # Save image
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate caption
        caption = generate_caption(file_path, model_name=model, prompt=prompt)

        # Save to DB
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
        print("❌ Upload error:", e)
        return {"error": str(e)}


@app.post("/api/generate-title")
async def generate_image_title(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    print(f"🚀 Upload received for titling: {file.filename}")

    try:
        # Save image
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate title (uses fixed prompt internally)
        title = generate_title(file_path)

        return {
            "filename": filename,
            "title": title
        }

    except Exception as e:
        print("❌ Title generation error:", e)
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
