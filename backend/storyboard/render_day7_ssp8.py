"""Render Day7 draft using diversified plan (SSP8 render step)

Uses Pexels (if configured) to fetch images for `stock_clip` scenes,
creates short motion clips using ffmpeg, builds comparison/diagram cards
with PIL for other modalities, and concatenates into a draft MP4.

Generated media is written under `backend/generated_videos/storyboard_review/day7_ssp8_render/` (gitignored).
"""
import os
import json
import requests
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_ROOT = Path(__file__).resolve().parents[1] / 'generated_videos' / 'storyboard_review' / 'day7_ssp8_render'
OUT_ROOT.mkdir(parents=True, exist_ok=True)
RAW = OUT_ROOT / 'raw'
RAW.mkdir(parents=True, exist_ok=True)

PLAN = Path(__file__).resolve().parents[1] / 'generated_videos' / 'storyboard_review' / 'scene_selection_plan_day7_diversified.json'

PEXELS_KEY = os.getenv('PEXELS_API_KEY') or os.getenv('PEXELS_KEY')


def fetch_pexels_image(query: str) -> bytes | None:
    if not PEXELS_KEY:
        return None
    try:
        headers = {'Authorization': PEXELS_KEY}
        params = {'query': query or 'coffee', 'per_page': 1}
        r = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            photos = data.get('photos') or []
            if photos:
                src = photos[0].get('src', {})
                url = src.get('large') or src.get('original')
                if url:
                    ir = requests.get(url, timeout=15)
                    if ir.status_code == 200:
                        return ir.content
    except Exception:
        return None
    return None


def make_image_from_bytes(b: bytes, out_path: Path):
    try:
        with open(out_path, 'wb') as f:
            f.write(b)
        return out_path
    except Exception:
        return None


def make_card(text: str, out_path: Path, size=(1080,1920), bg=(24,28,36)):
    img = Image.new('RGB', size, bg)
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('arial.ttf', 96)
    except Exception:
        f = ImageFont.load_default()
    try:
        bbox = d.textbbox((0,0), text, font=f)
        w = bbox[2]-bbox[0]
        h = bbox[3]-bbox[1]
    except Exception:
        try:
            w,h = d.textsize(text, font=f)
        except Exception:
            w,h = (len(text)*10, 20)
    d.text(((size[0]-w)/2,(size[1]-h)/2), text, font=f, fill=(255,255,255))
    img.save(out_path, quality=90)
    return out_path


def make_clip_from_image(img_path: Path, out_mp4: Path, duration=1.2):
    # create a simple kenburns effect using ffmpeg zoompan
    cmd = [
        'ffmpeg','-y','-loop','1','-i',str(img_path),'-c:v','libx264','-t',str(duration),'-pix_fmt','yuv420p',str(out_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_mp4


def render():
    if not PLAN.exists():
        print('Diversified plan missing:', PLAN)
        return
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    segs = []
    for s in plan:
        sid = s.get('scene_id') or 'scene'
        med = s.get('chosen_medium')
        fname = RAW / f"{sid}.jpg"
        mp4 = RAW / f"{sid}.mp4"
        if med == 'stock_clip':
            # try pexels
            b = fetch_pexels_image(s.get('asset_query_or_capture_instruction') or sid)
            if b:
                make_image_from_bytes(b, fname)
            else:
                make_card(sid, fname)
            make_clip_from_image(fname, mp4, duration=1.2)
        elif med in ('comparison_card','diagram_animation','payoff_card'):
            # generate card
            make_card(sid + '\n' + med, fname)
            make_clip_from_image(fname, mp4, duration=1.2)
        elif med == 'local_ai_prompt_capture' or med == 'playwright_browser_capture':
            make_card('PROMPT:\n'+(s.get('asset_query_or_capture_instruction') or ''), fname)
            make_clip_from_image(fname, mp4, duration=1.2)
        else:
            make_card(sid, fname)
            make_clip_from_image(fname, mp4, duration=1.2)
        segs.append(mp4)

    # concat
    concat_list = RAW / 'concat_list.txt'
    with open(concat_list, 'w', encoding='utf-8') as f:
        for p in segs:
            f.write(f"file '{p.as_posix()}'\n")

    out_file = OUT_ROOT / 'day7_coffee_scene_policy_anthropic_v1.mp4'
    cmd = ['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat_list),'-c','copy',str(out_file)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # contact sheet (single image of first frames)
    try:
        from PIL import Image
        thumbs = []
        for p in segs:
            # take first frame (we have jpgs)
            img = Image.open(p.with_suffix('.jpg')).convert('RGB')
            img.thumbnail((360,640))
            thumbs.append(img)
        cols = 3
        rows = (len(thumbs)+cols-1)//cols
        w = cols*360
        h = rows*640
        sheet = Image.new('RGB',(w,h),(14,18,26))
        for i,t in enumerate(thumbs):
            x = (i%cols)*360
            y = (i//cols)*640
            sheet.paste(t,(x,y))
        sheet.save(OUT_ROOT / 'contact_sheet.jpg', quality=90)
    except Exception:
        pass

    print('Rendered:', out_file)
    return out_file


if __name__ == '__main__':
    render()
