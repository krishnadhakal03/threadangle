#!/usr/bin/env python3
"""Generate sample frames for the Phase 3A long-form bill audit MVP draft.

Frame-only draft assets:
- no full long-form MP4 render
- no paid APIs
- no ElevenLabs or RunwayML
- local/demo data only
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920
BACKEND_DIR = Path(__file__).resolve().parent
OUT_DIR = BACKEND_DIR / "generated_videos" / "review" / "phase3a_longform_mvp_draft"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill, spacing: int = 8) -> None:
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) // 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing, align="center")


def base_bg() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (246, 248, 251))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        shade = 250 - int(y * 0.014)
        draw.line([(0, y), (WIDTH, y)], fill=(shade, min(255, shade + 1), min(255, shade + 4)))
    return img


def draw_browser(draw: ImageDraw.ImageDraw, url: str) -> tuple[int, int, int, int]:
    shell = (54, 116, 1026, 1510)
    draw.rounded_rectangle(shell, radius=34, fill=(255, 255, 255), outline=(210, 218, 230), width=3)
    draw.rounded_rectangle((54, 116, 1026, 240), radius=34, fill=(20, 28, 42))
    draw.rectangle((54, 178, 1026, 240), fill=(20, 28, 42))
    for idx, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        x = 92 + idx * 34
        draw.ellipse((x, 160, x + 20, 180), fill=color)
    draw.rounded_rectangle((210, 148, 950, 204), radius=18, fill=(245, 247, 250))
    draw.text((235, 160), url, font=font(28), fill=(71, 85, 105))
    return (82, 270, 998, 1452)


def draw_cursor(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    pts = [(x, y), (x, y + 52), (x + 16, y + 38), (x + 33, y + 69), (x + 48, y + 60), (x + 29, y + 33), (x + 52, y + 33)]
    draw.polygon(pts, fill=(15, 23, 42))
    draw.line(pts + [pts[0]], fill=(255, 255, 255), width=2)


def frame_hook() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (8, 13, 24))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((70, 280, 1010, 1260), radius=34, fill=(14, 24, 39), outline=(82, 196, 255), width=8)
    center_text(draw, (110, 360, 970, 470), "I USED AI TO AUDIT MY BILLS", font(52, True), (82, 196, 255))
    center_text(draw, (100, 545, 980, 760), "Most people think:\n$86 / MONTH", font(74, True), (255, 255, 255), 14)
    center_text(draw, (100, 865, 980, 1080), "Reality is often\nmuch higher", font(72, True), (255, 255, 255), 14)
    center_text(draw, (100, 1140, 980, 1215), "Run a 5-minute bill audit", font(42, True), (82, 196, 255))
    return img


def frame_inventory() -> Image.Image:
    img = base_bg()
    draw = ImageDraw.Draw(img)
    area = draw_browser(draw, "local-demo://bill-inventory")
    draw.text((area[0], area[1]), "Recurring bills inventory", font=font(54, True), fill=(15, 23, 42))
    headers = ["Service", "Monthly", "Use?"]
    xs = [area[0] + 24, area[0] + 500, area[0] + 760]
    y = area[1] + 105
    for x, label in zip(xs, headers):
        draw.text((x, y), label, font=font(32, True), fill=(71, 85, 105))
    rows = [
        ("Netflix", "$22.99", "Yes"),
        ("Hulu", "$17.99", "Maybe"),
        ("Spotify", "$11.99", "Yes"),
        ("Gym", "$39.99", "No"),
        ("Phone", "$95", "Yes"),
        ("Cloud", "$9.99", "Maybe"),
    ]
    y += 58
    for idx, row in enumerate(rows):
        top = y + idx * 116
        fill = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
        draw.rounded_rectangle((area[0], top, area[2], top + 88), radius=16, fill=fill, outline=(226, 232, 240), width=2)
        for x, text in zip(xs, row):
            draw.text((x, top + 24), text, font=font(38, True), fill=(15, 23, 42))
    draw_cursor(draw, area[0] + 725, y + 3 * 116 + 30)
    return img


def frame_prompt() -> Image.Image:
    img = base_bg()
    draw = ImageDraw.Draw(img)
    area = draw_browser(draw, "local-demo://ai-audit")
    draw.text((area[0], area[1]), "AI audit prompt", font=font(58, True), fill=(15, 23, 42))
    box = (area[0], area[1] + 130, area[2], area[1] + 700)
    draw.rounded_rectangle(box, radius=24, fill=(248, 250, 252), outline=(203, 213, 225), width=3)
    prompt = "Analyze these recurring expenses.\nFind overlaps, cheaper alternatives,\nand bills worth renegotiating."
    draw.multiline_text((box[0] + 36, box[1] + 56), prompt + "|", font=font(46, True), fill=(15, 23, 42), spacing=20)
    draw.rounded_rectangle((area[0], area[1] + 770, area[0] + 310, area[1] + 865), radius=22, fill=(37, 99, 235))
    center_text(draw, (area[0], area[1] + 770, area[0] + 310, area[1] + 865), "Run audit", font(36, True), (255, 255, 255))
    return img


def frame_reasoning() -> Image.Image:
    img = base_bg()
    draw = ImageDraw.Draw(img)
    area = draw_browser(draw, "local-demo://audit-results")
    draw.text((area[0], area[1]), "AI audit reasoning", font=font(54, True), fill=(15, 23, 42))
    items = [
        ("Overlap", "Netflix + Hulu"),
        ("Unused", "Gym marked No"),
        ("Renegotiate", "Phone at $95"),
        ("Downgrade", "Cloud storage"),
    ]
    for idx, (title, sub) in enumerate(items):
        top = area[1] + 130 + idx * 200
        draw.rounded_rectangle((area[0], top, area[2], top + 150), radius=24, fill=(255, 255, 255), outline=(203, 213, 225), width=3)
        draw.text((area[0] + 34, top + 28), title, font=font(42, True), fill=(15, 23, 42))
        draw.text((area[0] + 34, top + 88), sub, font=font(44, True), fill=(5, 150, 105))
    return img


def frame_negotiation() -> Image.Image:
    img = base_bg()
    draw = ImageDraw.Draw(img)
    area = draw_browser(draw, "local-demo://phone-script")
    draw.text((area[0], area[1]), "Phone bill workflow", font=font(56, True), fill=(15, 23, 42))
    draw.rounded_rectangle((area[0], area[1] + 105, area[2], area[1] + 325), radius=24, fill=(239, 246, 255), outline=(191, 219, 254), width=3)
    draw.text((area[0] + 30, area[1] + 135), "Call line", font=font(34, True), fill=(29, 78, 216))
    call = "Can you check whether I qualify\nfor a lower monthly plan or\nretention offer?"
    draw.multiline_text((area[0] + 30, area[1] + 185), call, font=font(38, True), fill=(15, 23, 42), spacing=12)
    checklist = ["Loyalty discount", "Lower plan", "Autopay discount", "Retention offer"]
    for idx, item in enumerate(checklist):
        top = area[1] + 410 + idx * 135
        draw.rounded_rectangle((area[0], top, area[2], top + 96), radius=20, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
        draw.ellipse((area[0] + 32, top + 28, area[0] + 72, top + 68), fill=(5, 150, 105))
        draw.text((area[0] + 100, top + 26), item, font=font(40, True), fill=(15, 23, 42))
    draw_cursor(draw, area[2] - 100, area[1] + 810)
    return img


def frame_savings() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((58, 140, 1022, 1370), radius=32, fill=(255, 255, 255), outline=(82, 196, 255), width=10)
    center_text(draw, (100, 215, 980, 320), "POSSIBLE SAVINGS", font(58, True), (15, 23, 42))
    center_text(draw, (100, 430, 980, 610), "$53 / MONTH", font(118, True), (5, 150, 105))
    draw.rounded_rectangle((100, 720, 980, 1010), radius=28, fill=(10, 16, 28))
    center_text(draw, (120, 750, 960, 890), "$636 / YEAR", font(112, True), (255, 255, 255))
    center_text(draw, (120, 908, 960, 962), "Example audit", font(36, True), (82, 196, 255))
    center_text(draw, (100, 1115, 980, 1260), "Verify before\nnext bill day", font(58, True), (15, 23, 42), 12)
    return img


def frame_cta() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (8, 13, 24))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((70, 350, 1010, 1260), radius=34, fill=(14, 24, 39), outline=(82, 196, 255), width=8)
    center_text(draw, (100, 450, 980, 615), "COMMENT AUDIT", font(80, True), (255, 255, 255))
    center_text(draw, (100, 700, 980, 850), "FULL PROMPT\n+ CHECKLIST", font(68, True), (82, 196, 255), 12)
    center_text(draw, (100, 990, 980, 1110), "Save for bill day", font(52, True), (255, 255, 255))
    return img


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frames = [
        ("scene_01_hook.jpg", frame_hook()),
        ("scene_02_inventory.jpg", frame_inventory()),
        ("scene_03_prompt.jpg", frame_prompt()),
        ("scene_04_reasoning.jpg", frame_reasoning()),
        ("scene_05_negotiation.jpg", frame_negotiation()),
        ("scene_06_savings.jpg", frame_savings()),
        ("scene_07_cta.jpg", frame_cta()),
    ]
    for name, image in frames:
        image.save(OUT_DIR / name, "JPEG", quality=92)

    thumbs = [image.resize((216, 384), Image.Resampling.LANCZOS) for _, image in frames]
    sheet = Image.new("RGB", (216 * len(thumbs), 384), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, (idx * 216, 0))
    sheet.save(OUT_DIR / "contact_sheet.jpg", "JPEG", quality=92)

    print(OUT_DIR)
    for name, _ in frames:
        print(OUT_DIR / name)
    print(OUT_DIR / "contact_sheet.jpg")


if __name__ == "__main__":
    main()
