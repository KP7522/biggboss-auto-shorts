import os
import asyncio
import subprocess
import requests
import random
import edge_tts
from PIL import Image, ImageDraw

# 1. DRAMATIC TELUGU SCRIPT TEMPLATES (NO API NEEDED)
TELUGU_SCRIPTS = [
    "Arey rey rey! Ee vaaram Bigg Boss house lo jargindi choosthe mee mind blank aipothundi! Evaru oohinchani twist! House lo game completely maaripoyindi. Danger zone lo unna contestant evaro telusa? Instant updates kosam Subscribe cheskondi!",
    "Bigg Boss house lo eeroju jarigina godava mamulugaledu! Housemates andaru rendu vargaalu ga maripoyaru. Nomination list lo pedda shocker ready ga undi. Ee vaaram evaru evict avtharo comment section lo cheppandi!",
    "House lo oka vaipu master plan, inko vaipu revenge game! Ee vaaram nominations lo evaru danger zone lo unnaro telusthe shock avtharu! Audience ga mee vote evarki vesthunnaro kinda comment cheyandi. Subscribe for daily updates!"
]

def get_script():
    # Randomly picks a high-energy Telugu commentary script
    return random.choice(TELUGU_SCRIPTS)

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
    print("Step 1: Fetching Telugu Script...")
    script = get_script()
    print(f"Script: {script[:40]}...")
    
    print("Step 2: Generating Telugu Audio Voiceover...")
    await generate_voiceover(script)
    
    print("Step 3: Fetching Images...")
    download_images()
    
    print("Step 4: Rendering Video with FFmpeg...")
    render_video()
    print("SUCCESS: Video created!")

if __name__ == "__main__":
    asyncio.run(main())
