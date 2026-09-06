import os
import asyncio
import json
import subprocess
import requests
from google import genai
import edge_tts
from PIL import Image

# 1. GENERATE TELUGU SCRIPT USING OFFICIAL GOOGLE GENAI SDK
def generate_script_and_keywords():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY secret is missing in GitHub Settings!")

    client = genai.Client(api_key=api_key)
    
    prompt = """
    You are a viral Telugu Bigg Boss reviewer. Write a 30-second high-energy dramatic commentary in Telugu script format for a YouTube Short / Reel.
    Structure:
    1. Hook / Shock (5s)
    2. Main House Drama / Conflict (15s)
    3. Call to Action - Subscribe / Comment (10s)

    Respond ONLY in valid JSON format with two keys:
    "script": "The Telugu commentary text to be spoken",
    "keywords": ["List", "of", "3", "English", "search", "keywords", "for", "images"]
    """
    
    # Updated model string to gemini-1.5-flash as explicitly requested by Google API error
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    data = json.loads(response.text)
    return data["script"], data["keywords"]

# 2. GENERATE TELUGU VOICE
async def generate_voiceover(text, output_path="voiceover.mp3"):
    communicate = edge_tts.Communicate(text, "te-IN-MohanNeural")
    await communicate.save(output_path)

# 3. PREPARE SAFE IMAGES
def download_images(keywords, output_dir="safe_images"):
    os.makedirs(output_dir, exist_ok=True)
    processed_files = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for idx in range(3):
        safe_path = os.path.join(output_dir, f"frame_{idx:03d}.jpg")
        url = "https://picsum.photos/1080/1920"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                with open("temp.jpg", "wb") as f:
                    f.write(res.content)
                img = Image.open("temp.jpg").transpose(Image.FLIP_LEFT_RIGHT).resize((1080, 1920))
                img.save(safe_path)
                if os.path.exists("temp.jpg"):
                    os.remove("temp.jpg")
            else:
                img = Image.new("RGB", (1080, 1920), color=(20, 20, 30))
                img.save(safe_path)
        except Exception:
            img = Image.new("RGB", (1080, 1920), color=(20, 20, 30))
            img.save(safe_path)
            
        processed_files.append(safe_path)
        
    return processed_files

# 4. RENDER VIDEO WITH FFMPEG
def render_video():
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "1/5", "-i", "safe_images/frame_%03d.jpg",
        "-i", "voiceover.mp3",
        "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "final_short.mp4"
    ]
    subprocess.run(cmd, check=True)

# MAIN PIPELINE
async def main():
    print("Step 1: Fetching Script from Gemini...")
    script, keywords = generate_script_and_keywords()
    
    print("Step 2: Generating Telugu Audio...")
    await generate_voiceover(script)
    
    print("Step 3: Preparing Images...")
    download_images(keywords)
    
    print("Step 4: Rendering Video...")
    render_video()
    print("SUCCESS: Video created!")

if __name__ == "__main__":
    asyncio.run(main())
