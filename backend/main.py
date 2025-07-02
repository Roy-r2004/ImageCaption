from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
import shutil
import uuid
from datetime import datetime

from .captioning import generate_caption
from .models import models
from .models.database import SessionLocal, engine, Base

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# FastAPI app instance
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload folder
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

@app.get("/api/message")
def get_message():
    return {"message": "Hello from FastAPI!"}

@app.post("/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    model: str = Form("blip"),
    db: Session = Depends(get_db)
):
    print(f"🚀 Received upload: {file.filename}")
    print(f"🧠 Requested model: {model}")

    try:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save image
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Generate caption
        caption = generate_caption(file_path, model_name=model)

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
            "model": model
        }

    except Exception as e:
        print("❌ Error during upload:", e)
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
