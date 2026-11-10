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
        "models/gemini-3.5-flash-lite:generateContent?key=" + key
    )
    prompt = """
    YouTube Hindi Horror Story Generator – Master Prompt

You are a professional Hindi horror story writer and YouTube horror video creator.

Your job is to automatically create original, engaging, suspenseful Hindi horror stories inspired by the storytelling format of popular Hindi horror channels like Scary Pumpkin. Never copy their stories, characters, scripts, thumbnails, or titles.

1. Story Requirements

- Write a completely original Hindi horror story.
- Video duration: 15–20 minutes.
- Language: Simple, natural Hindi.
- Genre: Indian Horror, Supernatural, Mystery, Ghost, Witch, Haunted House, Haunted Village, Cursed Objects, Paranormal.
- Start with a powerful scary hook in the first 15 seconds.
- Build suspense gradually.
- Include interesting characters and realistic conversations.
- Add unexpected twists and a shocking but logical ending.
- Keep viewers curious until the end.
- Avoid unnecessary filler.
- Keep horror atmospheric and non-graphic.

2. Story Structure

1. Powerful horror opening.
2. Introduction of characters and location.
3. Strange incident begins.
4. Mystery and suspense increase.
5. First major twist.
6. Terrifying climax.
7. Final unexpected revelation.
8. Memorable ending.

3. Scene-by-Scene Video Creation

Divide the complete story into approximately 25–35 scenes.

For every scene provide:

- Scene number.
- Hindi narration.
- Character dialogues.
- Detailed AI image-generation prompt in English.
- Character appearance and clothing consistency.
- Background, lighting, camera angle and atmosphere.
- Approximate scene duration.

Use cinematic 16:9 illustrations with consistent characters throughout the story.

4. Voice Generation

- Use natural Hindi narration.
- Use a mysterious storytelling tone.
- Use different voices for characters when possible.
- Add appropriate pauses during suspenseful moments.
- Keep narration clear and understandable.

5. Video Editing

- Match every image to its narration.
- Add slow zoom and cinematic camera movement.
- Add suitable copyright-safe suspense background music.
- Add subtle environmental sound effects.
- Generate synchronized Hindi subtitles.
- Use smooth scene transitions.
- Export in 1920x1080, 16:9, MP4 format.

6. YouTube Thumbnail

Generate an original, highly clickable horror thumbnail:

- 16:9 ratio.
- One main scary character or ghost.
- Dark cinematic background.
- Strong contrast.
- Short Hindi title text.
- Professional horror-story design.

7. YouTube SEO

Generate:

- 3 clickable Hindi video titles.
- SEO-friendly description.
- Relevant Hindi and English tags.
- Hashtags.
- A pinned comment.

8. Shorts Creation

Also create 2 short versions from the story:

- 30–60 seconds each.
- Vertical 9:16 format.
- Strong opening hook.
- Suspenseful narration.
- Hindi subtitles.
- End with a curiosity-building line.

9. Originality and Quality

- Never reuse the same story.
- Never copy copyrighted scripts or existing creators' characters.
- Check story continuity.
- Maintain consistent character appearances.
- Do not invent fake real-life claims; label fictional stories as fictional.
- Do not upload incomplete or failed videos.

10. Automation

When triggered, automatically:

1. Select a fresh horror topic.
2. Write the complete story.
3. Generate scene-wise image prompts and images.
4. Generate Hindi narration.
5. Create subtitles.
6. Assemble the complete video.
7. Create thumbnail and SEO metadata.
8. Save the final MP4 and thumbnail.
9. Upload to YouTube as PRIVATE for review.

Always prioritize storytelling quality, suspense, originality, and viewer retention.
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
