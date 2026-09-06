import os
import glob
import asyncio
import requests
import json
from google import genai
from PIL import Image, ImageDraw
import edge_tts
from moviepy import AudioFileClip, ImageSequenceClip

# 1. GENERATE TELUGU SCRIPT
def generate_script_and_keywords():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    prompt = """
    You are a viral Telugu Bigg Boss reviewer. Write a 45-second high-energy dramatic commentary in Telugu script format for a YouTube Short / Reel.
    Structure:
    1. Hook / Shock (5s)
    2. Main House Drama / Conflict (20s)
    3. Voting / Danger Zone Suspense (10s)
    4. Call to Action - Subscribe / Comment (10s)

    Respond ONLY in valid JSON format with two keys:
    "script": "The Telugu commentary text to be spoken",
    "keywords": ["List", "of", "4", "English", "search", "keywords", "for", "images"]
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    data = json.loads(response.text)
    return data["script"], data["keywords"]

# 2. GENERATE TELUGU VOICE
async def generate_voiceover(text, output_path="voiceover.mp3"):
    communicate = edge_tts.Communicate(text, "te-IN-MohanNeural")
    await communicate.save(output_path)

# CREATE FALLBACK IMAGE IF DOWNLOAD FAILS
def create_fallback_image(filename, text="Bigg Boss Telugu"):
    img = Image.new("RGB", (1080, 1920), color=(20, 20, 30))
    d = ImageDraw.Draw(img)
    d.text((300, 960), text, fill=(255, 255, 255))
    img.save(filename)

# 3. DOWNLOAD & PROCESS SAFE IMAGES
def download_and_process_images(keywords, output_dir="safe_images"):
    os.makedirs(output_dir, exist_ok=True)
    processed_files = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for idx, kw in enumerate(keywords):
        safe_path = os.path.join(output_dir, f"frame_{idx}.jpg")
        url = f"https://picsum.photos/1080/1920"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                raw_path = f"raw_{idx}.jpg"
                with open(raw_path, "wb") as f:
                    f.write(res.content)
                
                img = Image.open(raw_path)
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
                img = img.resize((1080, 1920))
                img.save(safe_path)
                processed_files.append(safe_path)
                if os.path.exists(raw_path):
                    os.remove(raw_path)
            else:
                create_fallback_image(safe_path, kw)
                processed_files.append(safe_path)
        except Exception as e:
            print(f"Image error on {kw}: {e}")
            create_fallback_image(safe_path, kw)
            processed_files.append(safe_path)
            
    return processed_files

# 4. ASSEMBLE VIDEO (MoviePy 2.0 Compatibility)
def render_video(audio_path, image_paths, output_path="final_short.mp4"):
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    if not image_paths:
        raise Exception("No images available for rendering.")
        
    duration_per_image = duration / len(image_paths)
    clip = ImageSequenceClip(image_paths, durations=[duration_per_image] * len(image_paths))
    
    # MoviePy 2.0 method update
    if hasattr(clip, "with_audio"):
        clip = clip.with_audio(audio)
    else:
        clip = clip.set_audio(audio)
        
    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

# EXECUTE PIPELINE
async def main():
    print("Step 1: Generating Telugu Script...")
    script, keywords = generate_script_and_keywords()
    
    print("Step 2: Generating Telugu Voiceover...")
    await generate_voiceover(script)
    
    print("Step 3: Downloading & Processing Safe Images...")
    image_paths = download_and_process_images(keywords)
    
    print("Step 4: Rendering Final MP4 Video...")
    render_video("voiceover.mp3", image_paths)
    print("SUCCESS: Video generated!")

if __name__ == "__main__":
    asyncio.run(main())
