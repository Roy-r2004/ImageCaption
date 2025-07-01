from fastapi import FastAPI, File, UploadFile, Depends
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

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app instance
app = FastAPI()

# CORS: allow frontend on localhost:4200
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

# Serve static images
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# Dependency to get DB session
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
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        caption = generate_caption(file_path)

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
            "caption": caption
        }

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