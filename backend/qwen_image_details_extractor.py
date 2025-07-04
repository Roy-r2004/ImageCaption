import base64
import requests
import re
import json
import os
from tkinter import filedialog, Tk

# === Configuration ===
# Get key from environment variable for security
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or "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"

QWEN_MODEL = "qwen/qwen2.5-vl-72b-instruct:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# === Static Prompt ===
PROMPT = """This is a product image. Analyze it carefully and respond ONLY in the following format:

Title: <short product name>
Tags: <comma-separated list of keywords>
Desc: <detailed and helpful product description>
Specs: <key specifications such as size, material, features, battery life, performance, etc. Use real product knowledge based on the image and search if needed>

Do NOT add anything else. Just respond in that exact format."""

# === Image Picker & Encoder ===
def get_base64_image():
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select a product image")
    if not path:
        print("❌ No image selected.")
        return None, None

    with open(path, "rb") as img_file:
        img_bytes = img_file.read()
        ext = path.split(".")[-1].lower()
        mime_type = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}", path

# === Qwen API Call ===
def query_qwen(base64_img):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": QWEN_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": base64_img}}
                ]
            }
        ]
    }

    # 🔍 Debug: Base64 preview
    print("\n🖼️ Base64 Image Preview:")
    print(base64_img[:100] + "...")

    # 🔍 Debug: Body preview
    print("\n📦 Request Body Preview:")
    print(json.dumps(body, indent=2)[:1000])  # truncate for readability

    response = requests.post(API_URL, headers=headers, json=body)

    # 🔍 Debug: Status and raw response
    print("\n🔁 HTTP Status:", response.status_code)
    print("📨 Raw Response:")
    print(response.text)

    response.raise_for_status()  # raises error if 400/500
    return response.json()["choices"][0]["message"]["content"]

# === Field Extractor ===
def extract_fields(text):
    pattern = r"Title:\s*(.*?)\nTags:\s*(.*?)\nDesc:\s*(.*?)\nSpecs:\s*(.*)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        print("❌ Could not extract structured response.")
        return None
    return {
        "Title": match.group(1).strip(),
        "Tags": match.group(2).strip(),
        "Desc": match.group(3).strip(),
        "Specs": match.group(4).strip()
    }

# === Main ===
def main():
    print("📤 Please select a product image...")
    base64_img, path = get_base64_image()
    if not base64_img:
        return

    print(f"🖼️ Selected image: {path}")

    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not found. Please set it using your terminal:")
        print("   export OPENROUTER_API_KEY=your_key_here   (Linux/macOS)")
        print("   set OPENROUTER_API_KEY=your_key_here      (Windows CMD)")
        return

    print("🚀 Sending image to Qwen model...")
    try:
        result_text = query_qwen(base64_img)

        print("\n📝 Raw AI Response:\n", result_text)

        fields = extract_fields(result_text)
        if fields:
            print("\n✅ Structured Output:")
            print(f"🔹 Title: {fields['Title']}")
            print(f"🔹 Tags:  {fields['Tags']}")
            print(f"🔹 Desc:  {fields['Desc']}")
            print(f"🔹 Specs: {fields['Specs']}")
    except Exception as e:
        print("❌ Error occurred:", e)

if __name__ == "__main__":
    main()
