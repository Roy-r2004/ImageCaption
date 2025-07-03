from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

# Load BLIP model and processor once
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

def generate_title(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")

    prompt = "a short and relevant title for this image:"
    inputs = processor(image, prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        output = model.generate(**inputs, max_length=16)
        full_output = processor.decode(output[0], skip_special_tokens=True)

    # Clean the output: remove everything before the colon
    if ":" in full_output:
        title = full_output.split(":")[-1].strip()
    else:
        title = full_output.strip()

    return title
