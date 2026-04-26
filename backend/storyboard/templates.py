from __future__ import annotations

from typing import Any

from .schema import Storyboard, StoryboardScene, VideoFormat, VisualSource


def money_proof_short(project_id: str, variables: dict[str, Any]) -> Storyboard:
    assets = variables.get("user_assets", {})
    return Storyboard(
        project_id=project_id,
        title=variables.get("title", "Money proof short"),
        niche=variables.get("niche", "personal finance"),
        template_id="money_proof_short",
        format=VideoFormat.short_9x16,
        render_mode=variables.get("render_mode", "draft"),
        variables=variables,
        scenes=[
            StoryboardScene(scene_id="hook", scene_type="hook", duration=4, narration_text=variables["hook_text"], caption_text=variables["hook_text"], visual_source=VisualSource.proof_screenshot, asset_path=assets.get("hook"), proof_label=variables.get("hook_label"), privacy_reviewed=True),
            StoryboardScene(scene_id="before_cost", scene_type="before_cost", duration=4, narration_text=variables["before_text"], caption_text=variables["before_text"], visual_source=VisualSource.generated_card, style={"headline": variables.get("before_card", "BEFORE")}),
            StoryboardScene(scene_id="ai_proof", scene_type="ai_proof", duration=6, narration_text=variables["proof_text"], caption_text=variables["proof_text"], visual_source=VisualSource.proof_screenshot, asset_path=assets.get("proof"), proof_label="Google AI found this", privacy_reviewed=True),
            StoryboardScene(scene_id="replacement_math", scene_type="replacement_math", duration=7, narration_text=variables["after_text"], caption_text=variables["after_text"], visual_source=VisualSource.proof_screenshot, asset_path=assets.get("after"), proof_label="AFTER", privacy_reviewed=True),
            StoryboardScene(scene_id="payoff", scene_type="payoff", duration=4, narration_text=variables["payoff_text"], caption_text=variables["payoff_text"], visual_source=VisualSource.generated_card, style={"headline": variables["proof_number"], "subline": variables.get("payoff_subline", "")}),
            StoryboardScene(scene_id="cta", scene_type="cta", duration=7, narration_text=variables["cta_text"], caption_text=variables["cta_text"], visual_source=VisualSource.generated_card, style={"bg": [9, 20, 36], "fg": [255, 255, 255], "accent": [52, 211, 153], "headline": f"COMMENT\n{variables.get('cta_word', 'INFO')}", "subline": "FOR THE PROMPT"}),
        ],
    )


def real_browser_proof_short(project_id: str, variables: dict[str, Any]) -> Storyboard:
    sb = money_proof_short(project_id, variables)
    sb.template_id = "real_browser_proof_short"
    sb.scenes[1].scene_type = "browser_search"
    sb.scenes[2].scene_type = "browser_proof"
    sb.scenes[2].visual_source = VisualSource.playwright_capture
    return sb


def build_tutorial_wide(project_id: str, variables: dict[str, Any]) -> Storyboard:
    scenes = []
    for scene_id, scene_type, text in [
        ("result", "final_result_first", variables.get("result_text", "Here is the final result.")),
        ("prompt", "prompt", variables.get("prompt_text", "This is the prompt.")),
        ("code", "code_generation", variables.get("code_text", "Then generate the code.")),
        ("terminal", "terminal", variables.get("terminal_text", "Run it in the terminal.")),
        ("browser", "browser_demo", variables.get("browser_text", "Check it in the browser.")),
        ("cta", "cta", variables.get("cta_text", "Follow for the build notes.")),
    ]:
        scenes.append(StoryboardScene(scene_id=scene_id, scene_type=scene_type, duration=5, narration_text=text, caption_text=text, visual_source=VisualSource.generated_card, style={"headline": text}))
    return Storyboard(project_id=project_id, title=variables.get("title", "Build tutorial"), niche="build", template_id="build_tutorial_wide", format=VideoFormat.wide_16x9, scenes=scenes)


TEMPLATES = {
    "money_proof_short": money_proof_short,
    "real_browser_proof_short": real_browser_proof_short,
    "build_tutorial_wide": build_tutorial_wide,
}
