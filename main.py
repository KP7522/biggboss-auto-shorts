import os
import glob
import asyncio
import requests
import json
from google import genai
from PIL import Image
import edge_tts
from moviepy.editor import AudioFileClip, ImageSequenceClip

# 1. GENERATE TELUGU SCRIPT
def generate_script_and_keywords():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
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

# 3. DOWNLOAD & PROCESS SAFE IMAGES
def download_and_process_images(keywords, output_dir="safe_images"):
    os.makedirs(output_dir, exist_ok=True)
    processed_files = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for idx, kw in enumerate(keywords):
        url = f"https://source.unsplash.com/1080x1920/?{kw},tv,drama"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                raw_path = f"raw_{idx}.jpg"
                with open(raw_path, "wb") as f:
                    f.write(res.content)
                
                img = Image.open(raw_path)
                img = img.transpose(Image.FLIP_LEFT_RIGHT) # Mirror image for copyright safety
                img = img.resize((1080, 1920))
                
                safe_path = os.path.join(output_dir, f"frame_{idx}.jpg")
                img.save(safe_path)
                processed_files.append(safe_path)
                os.remove(raw_path)
        except Exception as e:
            print(f"Image error: {e}")
            
    return processed_files

# 4. ASSEMBLE VIDEO
def render_video(audio_path, image_paths, output_path="final_short.mp4"):
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    if not image_paths:
        raise Exception("No images fetched for rendering.")
        
    duration_per_image = duration / len(image_paths)
    clip = ImageSequenceClip(image_paths, durations=[duration_per_image] * len(image_paths))
    clip = clip.set_audio(audio)
    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

# EXECUTE
async def main():
    print("Generating Telugu Script...")
    script, keywords = generate_script_and_keywords()
    
    print("Generating Telugu Voiceover...")
    await generate_voiceover(script)
    
    print("Downloading Images...")
    image_paths = download_and_process_images(keywords)
    
    print("Rendering Video...")
    render_video("voiceover.mp3", image_paths)
    print("DONE! Video created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
