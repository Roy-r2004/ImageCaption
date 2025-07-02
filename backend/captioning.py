from transformers import (
    BlipProcessor, BlipForConditionalGeneration,
    GitProcessor, GitForCausalLM
)
from PIL import Image
import torch

# Detect device
device = "cuda" if torch.cuda.is_available() else "cpu"

# ------------------- BLIP ------------------- #
print("🔧 Loading BLIP model...")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

def generate_blip_caption(image_path: str) -> str:
    print("🧠 Using BLIP model")
    image = Image.open(image_path).convert("RGB")
    inputs = blip_processor(image, return_tensors="pt").to(device)

    with torch.no_grad():
        output = blip_model.generate(**inputs)
        caption = blip_processor.decode(output[0], skip_special_tokens=True)

    return caption


# ------------------- GIT ------------------- #
print("🔧 Loading GIT model...")
git_processor = GitProcessor.from_pretrained("microsoft/git-base")
git_model = GitForCausalLM.from_pretrained("microsoft/git-base").to(device)

def generate_git_caption(image_path: str) -> str:
    print("🧠 Using GIT model")
    image = Image.open(image_path).convert("RGB")

    # Only pixel_values — no text prompt
    inputs = git_processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        generated_ids = git_model.generate(pixel_values=inputs.pixel_values, max_length=50)
        caption = git_processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

    return caption



# ------------------- Dispatcher ------------------- #
def generate_caption(image_path: str, model_name: str = "blip") -> str:
    model_name = model_name.lower()
    print(f"📥 Model selected: {model_name}")

    if model_name == "blip":
        return generate_blip_caption(image_path)
    elif model_name == "git":
        return generate_git_caption(image_path)
    else:
        raise ValueError(f"Unsupported model '{model_name}'. Choose from: blip, git.")
