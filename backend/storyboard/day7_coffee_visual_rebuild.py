"""
Day7 Coffee Visual Rebuild

Builds a real visual storyboard for the coffee savings video using local asset generation.
Generates custom proof images and saves a new storyboard JSON for rendering.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from backend.storyboard.formatting import font
from backend.storyboard.render import render_draft_video
from backend.storyboard.schema import (
    BeatRole,
    MotionIntensity,
    MotionProfile,
    RenderMode,
    Storyboard,
    StoryboardScene,
    VideoFormat,
    VisualSource,
)
from backend.storyboard.pattern_interrupts import apply_interrupt_rules, InterruptCadence
from backend.storyboard.semantic_emphasis import SemanticEmphasisEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "day7_coffee_visual_rebuild_v1" / "assets"
ASSET_ROOT.mkdir(parents=True, exist_ok=True)
STORYBOARD_PATH = REPO_ROOT / "backend" / "day7_coffee_visual_rebuild_storyboard.json"
OUTPUT_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "day7_coffee_visual_rebuild_v1"


def draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def create_gradient_background(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    width, height = size
    for y in range(height):
        ratio = y / max(1, height - 1)
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def make_coffee_cup_asset(path: Path) -> None:
    width, height = 1080, 1920
    img = create_gradient_background((width, height), (24, 20, 20), (50, 28, 10))
    draw = ImageDraw.Draw(img)

    cup_x, cup_y = 330, 520
    draw.rounded_rectangle((cup_x, cup_y, cup_x + 420, cup_y + 520), radius=120, fill=(240, 220, 180))
    draw.ellipse((cup_x + 80, cup_y + 80, cup_x + 340, cup_y + 260), fill=(255, 255, 255))
    draw.arc((cup_x + 160, cup_y + 260, cup_x + 360, cup_y + 420), 0, 180, fill=(112, 66, 20), width=18)
    draw.polygon([(cup_x + 70, cup_y + 420), (cup_x + 280, cup_y + 490), (cup_x + 380, cup_y + 430)], fill=(45, 35, 25))
    draw.arc((cup_x + 380, cup_y + 260, cup_x + 470, cup_y + 440), -90, 90, fill=(240, 220, 180), width=32)
    draw.line([(cup_x + 200, cup_y + 120), (cup_x + 240, cup_y + 100), (cup_x + 280, cup_y + 130), (cup_x + 320, cup_y + 110)], fill=(255, 245, 220), width=16)
    draw.line([(cup_x + 220, cup_y + 160), (cup_x + 260, cup_y + 140), (cup_x + 300, cup_y + 170)], fill=(255, 245, 220), width=12)

    card = (90, 1080, 990, 1500)
    draw.rounded_rectangle(card, radius=48, fill=(18, 30, 42))
    draw.rounded_rectangle(card, radius=48, fill=None, outline=(212, 255, 220), width=4)
    draw.text((160, 1120), "$5 A DAY", font=font(96, True), fill=(255, 255, 255))
    draw.text((160, 1248), "FOR COFFEE?", font=font(86, True), fill=(149, 233, 255))
    draw.text((160, 1390), "This was my daily spend.", font=font(44, False), fill=(211, 214, 255))
    img.save(path, quality=95)


def make_calculator_receipt_asset(path: Path) -> None:
    width, height = 1080, 1920
    img = create_gradient_background((width, height), (12, 16, 26), (35, 45, 70))
    draw = ImageDraw.Draw(img)

    receipt = (80, 260, 530, 1460)
    draw.rectangle(receipt, fill=(255, 255, 255))
    draw.line([(110, 340), (500, 340)], fill=(24, 28, 36), width=4)
    for idx, y in enumerate(range(420, 1420, 110)):
        draw.text((120, y), f"Item {idx + 1}  $5.00", font=font(34, False), fill=(30, 30, 30))
    draw.text((120, 1480), "30 days = $150", font=font(40, True), fill=(10, 10, 10))

    calc = (620, 360, 1000, 820)
    draw.rounded_rectangle(calc, radius=42, fill=(24, 28, 34))
    draw.rectangle((660, 420, 960, 520), fill=(248, 248, 255))
    draw.text((680, 438), "$150", font=font(60, True), fill=(10, 10, 30))
    for row in range(4):
        for col in range(3):
            x0 = 660 + col * 100
            y0 = 560 + row * 100
            draw.rectangle((x0, y0, x0 + 84, y0 + 84), fill=(40, 48, 60), outline=(86, 106, 166), width=2)
    draw.text((100, 80), "What was I paying?", font=font(72, True), fill=(255, 255, 255))
    draw.text((100, 170), "$5 x 30 = $150/month", font=font(56, True), fill=(255, 219, 77))
    img.save(path, quality=95)


def make_laptop_prompt_asset(path: Path) -> None:
    width, height = 1080, 1920
    img = create_gradient_background((width, height), (18, 22, 42), (10, 16, 32))
    draw = ImageDraw.Draw(img)

    browser = (70, 220, 1010, 1480)
    draw.rounded_rectangle(browser, radius=44, fill=(18, 24, 40))
    draw.rectangle((90, 245, 1000, 318), fill=(34, 42, 64))
    draw.ellipse((120, 265, 150, 295), fill=(255, 97, 97))
    draw.ellipse((170, 265, 200, 295), fill=(255, 203, 75))
    draw.ellipse((220, 265, 250, 295), fill=(129, 231, 231))
    draw.text((320, 266), "threadforge.ai / prompt", font=font(28, False), fill=(226, 229, 255))

    prompt_box = (120, 360, 980, 1040)
    draw.rounded_rectangle(prompt_box, radius=34, fill=(12, 20, 30))
    lines = [
        "I spend $5 a day on coffee.",
        "Compare that with brewing at home.",
        "Show monthly and yearly savings."
    ]
    for idx, line in enumerate(lines):
        draw.text((150, 400 + idx * 110), line, font=font(48, False), fill=(235, 241, 255))
    draw.rounded_rectangle((150, 1120, 430, 1200), radius=28, fill=(34, 94, 230))
    draw.text((180, 1140), "AI PROMPT", font=font(36, True), fill=(255, 255, 255))
    draw.text((100, 1500), "I asked AI what it would cost to make it at home.", font=font(46, False), fill=(255, 255, 255))
    img.save(path, quality=95)


def make_compare_asset(path: Path) -> None:
    width, height = 1080, 1920
    img = create_gradient_background((width, height), (8, 18, 34), (26, 40, 68))
    draw = ImageDraw.Draw(img)

    left = (50, 220, 520, 1420)
    right = (560, 220, 1030, 1420)
    draw.rounded_rectangle(left, radius=52, fill=(20, 28, 46))
    draw.rounded_rectangle(right, radius=52, fill=(26, 42, 70))
    draw.ellipse((150, 420, 420, 690), fill=(245, 225, 190))
    draw.rectangle((200, 520, 370, 720), fill=(55, 35, 20))
    draw.arc((390, 520, 470, 700), -90, 90, fill=(245, 225, 190), width=24)
    draw.text((140, 760), "Coffee shop", font=font(40, True), fill=(255, 255, 255))
    draw.text((140, 830), "$150/mo", font=font(68, True), fill=(253, 216, 53))
    draw.rounded_rectangle((660, 420, 930, 690), radius=40, fill=(245, 225, 190))
    draw.ellipse((690, 490, 780, 610), fill=(245, 225, 190))
    draw.text((660, 760), "Home brew", font=font(40, True), fill=(255, 255, 255))
    draw.text((660, 830), "$20/mo", font=font(68, True), fill=(134, 239, 172))
    draw.line((540, 260, 540, 1540), fill=(255, 255, 255, 80), width=4)
    draw.text((130, 170), "Face-off: coffee shop vs home", font=font(48, True), fill=(255, 255, 255))
    img.save(path, quality=95)


def make_reveal_asset(path: Path) -> None:
    width, height = 1080, 1920
    img = create_gradient_background((width, height), (8, 14, 30), (24, 32, 56))
    draw = ImageDraw.Draw(img)
    draw.text((120, 200), "Money difference", font=font(56, True), fill=(255, 255, 255))
    draw.text((120, 290), "$150 → $20", font=font(92, True), fill=(255, 219, 77))
    draw.rectangle((120, 520, 460, 1420), fill=(28, 40, 72))
    draw.rectangle((200, 820, 380, 1420), fill=(250, 179, 71))
    draw.rectangle((620, 920, 860, 1420), fill=(64, 207, 129))
    draw.text((160, 1450), "Coffee shop: $150", font=font(42, True), fill=(255, 255, 255))
    draw.text((640, 1450), "Home coffee: $20", font=font(42, True), fill=(255, 255, 255))
    draw.ellipse((820, 540, 980, 700), fill=(255, 255, 255, 180))
    draw.text((840, 580), "SAVE", font=font(44, True), fill=(18, 25, 33))
    draw.text((840, 640), "$130", font=font(72, True), fill=(18, 25, 33))
    img.save(path, quality=95)


def make_payoff_asset(path: Path) -> None:
    width, height = 1080, 1920
    img = create_gradient_background((width, height), (16, 20, 34), (10, 14, 22))
    draw = ImageDraw.Draw(img)
    draw.text((110, 260), "$1,500+", font=font(120, True), fill=(255, 255, 255))
    draw.text((110, 400), "/ YEAR", font=font(72, True), fill=(163, 255, 184))
    draw.text((110, 520), "Save about $130/month", font=font(50, False), fill=(207, 239, 255))
    for i in range(4):
        x = 120 + i * 170
        y = 960 - i * 40
        draw.rectangle((x, y, x + 140, y + 220), fill=(255, 209, 102), outline=(255, 255, 255), width=2)
    draw.text((110, 1240), "The year adds up fast.", font=font(42, False), fill=(224, 227, 255))
    img.save(path, quality=95)


def make_cta_asset(path: Path) -> None:
    width, height = 1080, 1920
    img = create_gradient_background((width, height), (16, 18, 30), (24, 32, 64))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((120, 240, 960, 1280), radius=52, fill=(18, 24, 40))
    draw.text((160, 320), "COMMENT COFFEE", font=font(84, True), fill=(255, 255, 255))
    draw.text((160, 420), "FOR THE PROMPT", font=font(46, False), fill=(163, 255, 184))
    draw.rounded_rectangle((220, 820, 520, 1100), radius=34, fill=(255, 255, 255))
    draw.text((240, 860), "I spend $5 a day on coffee.", font=font(32, False), fill=(18, 25, 33))
    draw.text((240, 920), "Compare that with brewing at home.", font=font(32, False), fill=(18, 25, 33))
    draw.text((240, 980), "Show monthly and yearly savings.", font=font(32, False), fill=(18, 25, 33))
    draw.ellipse((680, 980, 860, 1160), fill=(245, 220, 168))
    draw.arc((700, 1020, 840, 1160), 180, 360, fill=(124, 80, 21), width=24)
    img.save(path, quality=95)


def generate_assets() -> dict[str, str]:
    assets: dict[str, str] = {}
    mapping = {
        "hook": "hook_coffee_cup.png",
        "shock": "shock_calculator_receipt.png",
        "turn": "turn_laptop_prompt.png",
        "prompt": "prompt_browser_prompt.png",
        "reveal": "reveal_compare_savings.png",
        "payoff": "payoff_yearly_savings.png",
        "cta": "cta_coffee_prompt.png",
    }
    creators = {
        "hook": make_coffee_cup_asset,
        "shock": make_calculator_receipt_asset,
        "turn": make_laptop_prompt_asset,
        "prompt": make_compare_asset,
        "reveal": make_reveal_asset,
        "payoff": make_payoff_asset,
        "cta": make_cta_asset,
    }
    for scene_id, filename in mapping.items():
        path = ASSET_ROOT / filename
        if not path.exists():
            creators[scene_id](path)
        assets[scene_id] = str(path.relative_to(REPO_ROOT))
    return assets


def build_storyboard(assets: dict[str, str]) -> Storyboard:
    scene_data = [
        {
            "scene_id": "hook",
            "scene_type": "hook",
            "duration": 3.0,
            "narration_text": "I was spending $5 a day on coffee… and calling it a small treat.",
            "caption_text": "I was spending $5 a day on coffee… and calling it a small treat.",
            "visual_source": VisualSource.proof_screenshot,
            "asset_path": assets["hook"],
            "proof_label": "coffee shop",
            "motion_profile": MotionProfile.fireship_dynamic,
            "motion_intensity": MotionIntensity.high,
            "micro_beats": ["punch_zoom", "proof_flash", "shake_pan"],
            "beat_role": BeatRole.hook,
            "interrupt_allowed": True,
            "visual_layers": [
                'caption_layer:::{"font_size":78,"color":"white","max_width":900}:$5 A DAY\nFOR COFFEE?'
            ],
        },
        {
            "scene_id": "shock",
            "scene_type": "setup",
            "duration": 3.0,
            "narration_text": "That was $150 a month.",
            "caption_text": "That was $150 a month.",
            "visual_source": VisualSource.proof_screenshot,
            "asset_path": assets["shock"],
            "proof_label": "receipt math",
            "motion_profile": MotionProfile.fireship_dynamic,
            "motion_intensity": MotionIntensity.high,
            "micro_beats": ["value_tick", "snap_zoom", "freeze_emphasis"],
            "beat_role": BeatRole.setup,
            "interrupt_allowed": True,
            "visual_layers": [
                'caption_layer:::{"font_size":66,"color":"#ffdd66","max_width":900}:$5 x 30 = $150/month'
            ],
        },
        {
            "scene_id": "turn",
            "scene_type": "proof",
            "duration": 3.0,
            "narration_text": "So I asked AI what it would cost to make it at home.",
            "caption_text": "So I asked AI what it would cost to make it at home.",
            "visual_source": VisualSource.proof_screenshot,
            "asset_path": assets["turn"],
            "proof_label": "prompt capture",
            "motion_profile": MotionProfile.documentary_dynamic,
            "motion_intensity": MotionIntensity.high,
            "micro_beats": ["text_snap", "pulse_glow", "proof_flash"],
            "beat_role": BeatRole.proof,
            "interrupt_allowed": True,
            "visual_layers": [
                'caption_layer:::{"font_size":60,"color":"white","max_width":900}:Ask AI what it would cost to make it at home.'
            ],
        },
        {
            "scene_id": "prompt",
            "scene_type": "proof",
            "duration": 5.0,
            "narration_text": "I spend $5 a day on coffee. Compare that with brewing at home. Show monthly and yearly savings.",
            "caption_text": "I spend $5 a day on coffee. Compare that with brewing at home. Show monthly and yearly savings.",
            "visual_source": VisualSource.proof_screenshot,
            "asset_path": assets["prompt"],
            "proof_label": "AI prompt",
            "motion_profile": MotionProfile.fireship_dynamic,
            "motion_intensity": MotionIntensity.high,
            "micro_beats": ["typing", "magnifier_crop", "proof_flash"],
            "beat_role": BeatRole.proof,
            "interrupt_allowed": True,
            "visual_layers": [],
        },
        {
            "scene_id": "reveal",
            "scene_type": "proof",
            "duration": 4.0,
            "narration_text": "Coffee shop: $150/month. Home coffee: about $20/month.",
            "caption_text": "Coffee shop: $150/month. Home coffee: about $20/month.",
            "visual_source": VisualSource.proof_screenshot,
            "asset_path": assets["reveal"],
            "proof_label": "savings reveal",
            "motion_profile": MotionProfile.fireship_dynamic,
            "motion_intensity": MotionIntensity.high,
            "micro_beats": ["punch_zoom", "freeze_emphasis", "flash_cut"],
            "beat_role": BeatRole.proof,
            "interrupt_allowed": True,
            "visual_layers": [],
        },
        {
            "scene_id": "payoff",
            "scene_type": "payoff",
            "duration": 4.0,
            "narration_text": "Save about $130/month — over $1,500/year.",
            "caption_text": "Save about $130/month — over $1,500/year.",
            "visual_source": VisualSource.proof_screenshot,
            "asset_path": assets["payoff"],
            "proof_label": "yearly savings",
            "motion_profile": MotionProfile.documentary_dynamic,
            "motion_intensity": MotionIntensity.med,
            "micro_beats": ["punch_zoom", "proof_flash"],
            "beat_role": BeatRole.payoff,
            "interrupt_allowed": False,
            "visual_layers": [],
        },
        {
            "scene_id": "cta",
            "scene_type": "cta",
            "duration": 3.0,
            "narration_text": "Comment COFFEE and I’ll send the prompt.",
            "caption_text": "Comment COFFEE and I’ll send the prompt.",
            "visual_source": VisualSource.proof_screenshot,
            "asset_path": assets["cta"],
            "proof_label": "comment to get it",
            "motion_profile": MotionProfile.fireship_dynamic,
            "motion_intensity": MotionIntensity.high,
            "micro_beats": ["snap_zoom", "pulse_glow"],
            "beat_role": BeatRole.cta,
            "interrupt_allowed": True,
            "visual_layers": [],
        },
    ]

    storyboard = Storyboard(
        project_id="day7_coffee_visual_rebuild_v1",
        title="Coffee Savings Visual Rebuild",
        niche="personal finance",
        template_id="coffee_visual_rebuild",
        format=VideoFormat.short_9x16,
        render_mode=RenderMode.draft,
        style={"accent": [255, 210, 80]},
        variables={},
        scenes=[StoryboardScene(**data) for data in scene_data],
    )

    engine = SemanticEmphasisEngine()
    for scene in storyboard.scenes:
        engine.apply_semantic_emphasis(scene)

    apply_interrupt_rules(storyboard.scenes, InterruptCadence.fireship50)
    return storyboard


def save_storyboard(storyboard: Storyboard, path: Path) -> None:
    path.write_text(json.dumps(storyboard.model_dump(mode="json"), indent=2), encoding="utf-8")


def main() -> None:
    assets = generate_assets()
    storyboard = build_storyboard(assets)
    save_storyboard(storyboard, STORYBOARD_PATH)
    print(f"Saved storyboard to {STORYBOARD_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = render_draft_video(storyboard, REPO_ROOT, OUTPUT_DIR)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
