import os
import asyncio
import subprocess
import requests
import re
import edge_tts
from PIL import Image, ImageDraw

# 1. FETCH LIVE TELUGU BIGG BOSS UPDATES FROM THE WEB
def get_live_script():
    try:
        # Fetch live news snippets about Bigg Boss Telugu
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://news.google.com/rss/search?q=Bigg+Boss+Telugu&hl=te&gl=IN&ceid=IN:te", headers=headers, timeout=10)
        
        # Extract Telugu text headlines from RSS feed
        titles = re.findall(r'<title>(.*?)</title>', res.text)
        valid_titles = [t for t in titles if "Bigg Boss" in t or "బిగ్ బాస్" in t]
        
        if valid_titles:
            headline = valid_titles[0].split("-")[0].strip()
            script = f"Bigg Boss Telugu latest updates! {headline}. Ee vaaram house lo em jaragabothundho telusukovadaniki channel ki Subscribe cheskondi!"
            return script
    except Exception as e:
        print(f"Live fetch fallback: {e}")
        
    # Fallback script if web fetch fails
    return "Arey rey rey! Ee vaaram Bigg Boss house lo jargindi choosthe mee mind blank aipothundi! Evaru oohinchani twist! Instant updates kosam Subscribe cheskondi!"

# 2. GENERATE TELUGU VOICE
async def generate_voiceover(text, output_path="voiceover.mp3"):
    communicate = edge_tts.Communicate(text, "te-IN-MohanNeural")
    await communicate.save(output_path)

# 3. PREPARE SAFE IMAGES
def download_images(output_dir="safe_images"):
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

# 4. RENDER UNIVERSAL MP4 (FIXES HEVC / PLAYER COMPATIBILITY)
def render_video():
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "1/5", "-i", "safe_images/frame_%03d.jpg",
        "-i", "voiceover.mp3",
        "-c:v", "libx264",
        "-profile:v", "main",      # Forces standard universal H.264 profile
        "-pix_fmt", "yuv420p",      # Standard color format compatible with all free media players
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "final_short.mp4"
    ]
    subprocess.run(cmd, check=True)

# MAIN PIPELINE
async def main():
    print("Step 1: Fetching Live Telugu Bigg Boss News...")
    script = get_live_script()
    print(f"Script: {script}")
    
    print("Step 2: Generating Telugu Audio Voiceover...")
    await generate_voiceover(script)
    
    print("Step 3: Fetching Images...")
    download_images()
    
    print("Step 4: Rendering Universal MP4 Video...")
    render_video()
    print("SUCCESS: Standard MP4 Video created!")

if __name__ == "__main__":
    asyncio.run(main())
