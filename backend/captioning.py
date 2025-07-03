import torch
from PIL import Image
from transformers import (
    BlipProcessor, BlipForConditionalGeneration,
    GitProcessor, GitForCausalLM,
    Blip2Processor, Blip2ForConditionalGeneration
)

# ======================
# 🚀 Device Setup
# ======================
device = "cuda" if torch.cuda.is_available() else "cpu"

# ======================
# 🔧 Load Models Once
# ======================

# BLIP (base)
print("🔧 Loading BLIP model...")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
).to(device)

# GIT (TextCaps)
print("🔧 Loading GIT-Large TextCaps model...")
git_processor = GitProcessor.from_pretrained("microsoft/git-large-textcaps")
git_model = GitForCausalLM.from_pretrained("microsoft/git-large-textcaps").to(device)

# BLIP-2 (FLAN-T5)
print("🔧 Loading BLIP-2 FLAN-T5 model...")
blip2_processor = Blip2Processor.from_pretrained("Salesforce/blip2-flan-t5-xl")
blip2_model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-flan-t5-xl",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
).to(device)

# ======================
# 🧠 Captioning Functions
# ======================

def generate_blip_caption(image_path: str) -> str:
    print("🧠 Generating with BLIP...")
    image = Image.open(image_path).convert("RGB")
    inputs = blip_processor(image, return_tensors="pt").to(device)

    with torch.no_grad():
        output = blip_model.generate(**inputs)
        caption = blip_processor.decode(output[0], skip_special_tokens=True)

    return caption.strip()


def generate_git_caption(image_path: str) -> str:
    print("🧠 Generating with GIT-Large (TextCaps)...")
    image = Image.open(image_path).convert("RGB")
    inputs = git_processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        output = git_model.generate(pixel_values=inputs.pixel_values, max_length=50)
        caption = git_processor.batch_decode(output, skip_special_tokens=True)[0]

    return caption.strip()


def generate_blip2_caption(image_path: str, prompt: str = "Describe the image.") -> str:
    print(f"🧠 Generating with BLIP-2 FLAN-T5 | Prompt: '{prompt}'")
    image = Image.open(image_path).convert("RGB")
    inputs = blip2_processor(images=image, text=prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        output = blip2_model.generate(**inputs, max_new_tokens=100)
        caption = blip2_processor.tokenizer.decode(output[0], skip_special_tokens=True)

    return caption.strip()

# ======================
# 🔀 Model Dispatcher
# ======================

def generate_caption(image_path: str, model_name: str = "blip", prompt: str = "Describe the image.") -> str:
    model_name = model_name.lower()
    print(f"📥 Model selected: {model_name}")

    if model_name == "blip2":
        return generate_blip2_caption(image_path, prompt)
    elif model_name == "blip":
        return generate_blip_caption(image_path)
    elif model_name == "git":
        return generate_git_caption(image_path)
    else:
        raise ValueError(f"❌ Unsupported model '{model_name}'. Choose from: blip, git, blip2.")
