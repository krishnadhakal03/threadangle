"""Diversify repaired plans to avoid consecutive same-medium rejects.

This script loads the repaired plans produced by SSP8, swaps some
sequential `stock_clip` sequences to alternative modalities (comparison_card,
diagram_animation, local_ai_prompt_capture) where allowed, and re-runs
the critic. Writes diversified plans and critic reports.
"""
import json
from pathlib import Path
from dotenv import load_dotenv

from backend.storyboard import provider_availability, scene_critic

load_dotenv('backend/.env')

OUT = Path(__file__).resolve().parents[1] / 'generated_videos' / 'storyboard_review'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(obj, path: Path):
    path.write_text(json.dumps(obj, indent=2), encoding='utf-8')


def diversify(plan):
    providers = provider_availability.check_providers()
    play = providers.get('playwright_sandbox_profile')
    pex = providers.get('pexels_configured')
    pix = providers.get('pixabay_configured')

    alternates = ['comparison_card', 'diagram_animation']
    if play:
        alternates.append('playwright_browser_capture')
    else:
        alternates.append('local_ai_prompt_capture')

    out = []
    for i, s in enumerate(plan):
        prev = out[-1] if out else None
        new = dict(s)
        if prev and prev.get('chosen_medium') == s.get('chosen_medium'):
            # try to pick an alternate not equal to prev or next
            for alt in alternates:
                if alt != prev.get('chosen_medium'):
                    new['chosen_medium'] = alt
                    new.setdefault('why_this_medium', '')
                    new['why_this_medium'] = (new.get('why_this_medium') or '') + ' | diversified: set to ' + alt
                    break
        out.append(new)
    return out


def run():
    day6_in = OUT / 'scene_selection_plan_day6_repaired.json'
    day7_in = OUT / 'scene_selection_plan_day7_repaired.json'
    if not day6_in.exists() or not day7_in.exists():
        print('Repaired plans missing; run SSP8 first')
        return

    p6 = load(day6_in)
    p7 = load(day7_in)

    d6 = diversify(p6)
    d7 = diversify(p7)

    d6_path = OUT / 'scene_selection_plan_day6_diversified.json'
    d7_path = OUT / 'scene_selection_plan_day7_diversified.json'
    save(d6, d6_path)
    save(d7, d7_path)

    c6 = scene_critic.run_critic(d6)
    c7 = scene_critic.run_critic(d7)
    save(c6, OUT / 'critic_report_day6_diversified.json')
    save(c7, OUT / 'critic_report_day7_diversified.json')

    manifest = {
        'day6': {'plan': str(d6_path), 'critic': str(OUT / 'critic_report_day6_diversified.json')},
        'day7': {'plan': str(d7_path), 'critic': str(OUT / 'critic_report_day7_diversified.json')},
    }
    save(manifest, OUT / 'ssp8_diversify_manifest.json')
    print('Diversify manifest written:', OUT / 'ssp8_diversify_manifest.json')
    return OUT / 'ssp8_diversify_manifest.json'


if __name__ == '__main__':
    run()
