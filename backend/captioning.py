from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

# Load the model + processor once when the app starts
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def generate_caption(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt")

    with torch.no_grad():
        out = model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True)

    return caption
