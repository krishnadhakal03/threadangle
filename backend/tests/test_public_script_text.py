from utils.public_script_text import sanitize_public_script_text, sanitize_public_scene, sanitize_public_scenes


def test_sanitize_public_script_text_strips_workflow_labels():
    assert sanitize_public_script_text("Hook: STOP PAYING FOR AI") == "STOP PAYING FOR AI"
    assert sanitize_public_script_text("Body: Use these free tools") == "Use these free tools"
    assert sanitize_public_script_text("CTA: FOLLOW FOR MORE") == "FOLLOW FOR MORE"


def test_sanitize_public_script_text_strips_step_and_payoff_labels():
    assert sanitize_public_script_text("PAYOFF 1: Writing + research") == "Writing + research"
    assert sanitize_public_script_text("Step one: Open the app") == "Open the app"
    assert sanitize_public_script_text("Intro. PAYOFF 2: Images + design") == "Intro. Images + design"


def test_sanitize_public_scene_sanitizes_common_public_fields():
    scene = {
        "caption_text": "PAYOFF 3: Video + audio",
        "narration_text": "CTA: FOLLOW FOR THE FULL LIST",
        "visual_description": "Do not alter visual descriptions",
    }
    sanitized = sanitize_public_scene(scene)
    assert sanitized["caption_text"] == "Video + audio"
    assert sanitized["narration_text"] == "FOLLOW FOR THE FULL LIST"
    assert sanitized["visual_description"] == "Do not alter visual descriptions"


def test_sanitize_public_scenes_list():
    scenes = [{"script": "Hook: One idea"}, {"script": "PAYOFF 1: Another idea"}]
    assert sanitize_public_scenes(scenes) == [{"script": "One idea"}, {"script": "Another idea"}]
