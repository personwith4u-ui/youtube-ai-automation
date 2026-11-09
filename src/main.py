import os
import re
import json
import asyncio
import subprocess
import requests
import edge_tts
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path("output")
OUT.mkdir(exist_ok=True)

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

def make_script():
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.0-flash:generateContent?key=" + GEMINI_KEY
    )
    prompt = """
    Write an original interesting Hindi YouTube video script.
    Topic: Interesting facts about space.
    Give a catchy title and 6 short narration paragraphs.
    Return JSON only: {"title":"...", "scenes":["...", "..."]}
    """
    r = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    }, timeout=60)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)

def get_images(query):
    headers = {"Authorization": PEXELS_KEY}
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers=headers,
        params={"query": query, "per_page": 6},
        timeout=30
    )
    r.raise_for_status()
    photos = r.json()["photos"]
    if not photos:
        raise RuntimeError("Pexels par images nahi mili.")
    paths = []
    for i, photo in enumerate(photos):
        data = requests.get(photo["src"]["large"], timeout=30)
        data.raise_for_status()
        path = OUT / f"image_{i}.jpg"
        path.write_bytes(data.content)
        paths.append(path)
    return paths

async def make_voice(text):
    voice = edge_tts.Communicate(
        text, "hi-IN-MadhurNeural", rate="+0%"
    )
    await voice.save(str(OUT / "voice.mp3"))

def make_video(images):
    for i, path in enumerate(images):
        img = Image.open(path).convert("RGB")
        img = img.resize((1280, 720))
        img.save(OUT / f"frame_{i:03}.jpg")

    audio = OUT / "voice.mp3"
    frames = OUT / "frame_%03d.jpg"
    video = OUT / "video.mp4"

    subprocess.run([
        "ffmpeg", "-y", "-framerate", "1",
        "-i", str(frames), "-i", str(audio),
        "-vf", "format=yuv420p",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", str(video)
    ], check=True)

def main():
    if not GEMINI_KEY or not PEXELS_KEY:
        raise RuntimeError("API keys GitHub Secrets mein add karo.")

    data = make_script()
    narration = " ".join(data["scenes"])
    (OUT / "script.txt").write_text(
        data["title"] + "\n\n" + narration,
        encoding="utf-8"
    )

    images = get_images("space planets galaxy")
    asyncio.run(make_voice(narration))
    make_video(images)
    print("Video ready:", OUT / "video.mp4")

if __name__ == "__main__":
    main()
