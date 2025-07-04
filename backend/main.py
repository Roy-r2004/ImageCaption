from fastapi import FastAPI, File, UploadFile, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
import shutil
import uuid
from datetime import datetime
import requests
import json

from .models import models
from .models.database import SessionLocal, engine, Base
from .base64Conv import image_to_base64

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
    product: str = Form(...),
    db: Session = Depends(get_db)
):
    print(f"🚀 Received upload: {file.filename}")

    try:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save image
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        fileBase64 = image_to_base64(file_path)
        
        if product == '':
            prompt = """This is a product image. Analyze it carefully and respond ONLY in the following format:
            
            Title: <short product name>
            Tags: <comma-separated list of keywords>
            Desc: <detailed and helpful product description>
            Specs: <key specifications such as size, material, features, battery life, performance, etc. Use real product knowledge based on the image and search if needed>
            
            Do NOT add anything else. Just respond in that exact format."""
        else:
            prompt = """This is a product image. The user provided a keyword that might be useful to identify the product in the image. This keyword is """ + product  + """. Analyze the image carefully and respond ONLY in the following format:
            
            Title: <short product name>
            Tags: <comma-separated list of keywords>
            Desc: <detailed and helpful product description>
            Specs: <key specifications such as size, material, features, battery life, performance, etc. Use real product knowledge based on the image and search if needed>
            
            Do NOT add anything else. Just respond in that exact format."""
        
        
        print(prompt)

        response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer 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",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "qwen/qwen2.5-vl-32b-instruct:free",
            "messages": [
            {
                "role": "user",
                "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                    "url": fileBase64
                    }
                }
                ]
            }
            ],
            
        })
        )

        processed_text = response.json()["choices"][0]["message"]["content"]
        # Save to DB
        # new_entry = models.ImageCaption(
        #     filename=filename,
        #     caption=processed_text,
        #     timestamp=datetime.utcnow()
        # )
        # db.add(new_entry)
        # db.commit()
        # db.refresh(new_entry)

        return {
            "filename": filename,
            "caption": processed_text
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