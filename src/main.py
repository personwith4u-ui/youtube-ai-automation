import os
import json
import re
import asyncio
import subprocess
import requests
import edge_tts
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path("output")
OUT.mkdir(exist_ok=True)

def make_script():
    key = os.environ["GEMINI_API_KEY"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash:generateContent?key=" + key
    )
    prompt = """
    Write an original Hindi YouTube script about space facts.
    Give 6 interesting narration paragraphs.
    Return JSON only: {"title":"...", "scenes":["...", "..."]}
    """
    r = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    }, timeout=60)
    r.raise_for_status()
    data = r.json()
    result = data["candidates"][0]["content"]["parts"][0]["text"]
    result = re.sub(r"```json|```", "", result).strip()
    return json.loads(result)

def make_background():
    img = Image.new("RGB", (1280, 720), (12, 18, 55))
    draw = ImageDraw.Draw(img)

    for x, y, radius in [
        (200, 180, 100), (1000, 500, 160),
        (650, 300, 70), (900, 100, 35)
    ]:
        draw.ellipse(
            (x-radius, y-radius, x+radius, y+radius),
            fill=(35, 55, 125)
        )

    for x, y in [(100,100),(400,500),(700,100),
                 (1100,250),(500,650),(850,600)]:
        draw.ellipse((x,y,x+5,y+5), fill="white")

    img.save(OUT / "background.jpg")

async def make_voice(text):
    voice = edge_tts.Communicate(
        text, "hi-IN-MadhurNeural"
    )
    await voice.save(str(OUT / "voice.mp3"))

def make_video():
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(OUT / "background.jpg"),
        "-i", str(OUT / "voice.mp3"),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(OUT / "video.mp4")
    ], check=True)

def main():
    data = make_script()
    narration = " ".join(data["scenes"])

    (OUT / "script.txt").write_text(
        data["title"] + "\n\n" + narration,
        encoding="utf-8"
    )

    make_background()
    asyncio.run(make_voice(narration))
    make_video()

    print("Video ready:", OUT / "video.mp4")

if __name__ == "__main__":
    main()
