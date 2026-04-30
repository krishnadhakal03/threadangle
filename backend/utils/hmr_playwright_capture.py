"""Deterministic Playwright screenshots for HMR scene assets.

The helpers here are intentionally small and independent from the old
``browser_capture.py`` path because that module imports ``video_pipeline.py``.
No remote pages, accounts, or paid providers are used.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _safe_json(value: Any) -> str:
    return html.escape(json.dumps(value, ensure_ascii=False), quote=True)


def _receipt_audit_html(scene: dict[str, Any], width: int, height: int) -> str:
    prompt = _clean_text(scene.get("prompt") or "Find cheaper swaps for these repeat grocery items.")
    rows = scene.get("swap_rows") or [
        ("Brand cereal", "$8.49", "store brand", "$4.19"),
        ("Snack packs", "$11.80", "bulk bag", "$6.40"),
        ("Drinks", "$13.20", "home pack", "$7.10"),
    ]
    savings = _clean_text(scene.get("savings_number") or "$40/week")
    data = {
        "prompt": prompt,
        "rows": [list(row) for row in rows[:3]],
        "savings": savings,
    }
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={width}, initial-scale=1">
<title>Receipt Audit Capture</title>
<style>
* {{ box-sizing: border-box; }}
html, body {{
  width: {width}px;
  height: {height}px;
  margin: 0;
  overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  color: #121826;
  background:
    radial-gradient(circle at 22% 10%, rgba(47, 133, 90, 0.22), transparent 34%),
    linear-gradient(180deg, #ecf5ee 0%, #dfe8e4 42%, #d3ddd8 100%);
}}
.stage {{
  width: {width}px;
  height: {height}px;
  padding: {int(height * 0.075)}px {int(width * 0.065)}px;
  position: relative;
}}
.desk {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 42%;
  background:
    linear-gradient(90deg, rgba(255,255,255,0.18), transparent 24%, rgba(0,0,0,0.08)),
    linear-gradient(180deg, #cab89a, #a98762);
}}
.receipt {{
  position: absolute;
  left: {int(width * 0.055)}px;
  top: {int(height * 0.13)}px;
  width: {int(width * 0.31)}px;
  min-height: {int(height * 0.55)}px;
  padding: {int(width * 0.038)}px;
  background: #fffdf4;
  border: 1px solid rgba(88, 74, 50, 0.16);
  box-shadow: 0 {int(height * 0.012)}px {int(width * 0.04)}px rgba(46, 36, 20, 0.24);
  transform: rotate(-4deg);
}}
.receipt h2 {{
  margin: 0 0 {int(height * 0.018)}px;
  font-size: {int(width * 0.038)}px;
  letter-spacing: 0;
}}
.line {{
  display: flex;
  justify-content: space-between;
  border-bottom: 1px dashed rgba(90, 82, 64, 0.34);
  padding: {int(height * 0.009)}px 0;
  font-size: {int(width * 0.026)}px;
}}
.phone {{
  position: absolute;
  right: {int(width * 0.055)}px;
  top: {int(height * 0.07)}px;
  width: {int(width * 0.62)}px;
  height: {int(height * 0.78)}px;
  border-radius: {int(width * 0.055)}px;
  background: #111827;
  padding: {int(width * 0.024)}px;
  box-shadow: 0 {int(height * 0.022)}px {int(width * 0.08)}px rgba(15, 23, 42, 0.34);
}}
.screen {{
  height: 100%;
  border-radius: {int(width * 0.038)}px;
  overflow: hidden;
  background: #f8fafc;
  border: 1px solid #334155;
}}
.bar {{
  height: {int(height * 0.075)}px;
  background: #0f172a;
  color: #cbd5e1;
  display: flex;
  align-items: center;
  gap: {int(width * 0.012)}px;
  padding: 0 {int(width * 0.032)}px;
  font-size: {int(width * 0.026)}px;
  font-weight: 700;
}}
.dot {{ width: {int(width * 0.014)}px; height: {int(width * 0.014)}px; border-radius: 50%; }}
.content {{ padding: {int(height * 0.026)}px {int(width * 0.034)}px; }}
.eyebrow {{
  font-size: {int(width * 0.025)}px;
  color: #16704f;
  font-weight: 800;
  text-transform: uppercase;
}}
.title {{
  margin-top: {int(height * 0.010)}px;
  font-size: {int(width * 0.048)}px;
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: 0;
}}
.prompt {{
  margin-top: {int(height * 0.023)}px;
  padding: {int(height * 0.018)}px {int(width * 0.028)}px;
  border-radius: {int(width * 0.018)}px;
  background: #111827;
  color: #f8fafc;
  font-size: {int(width * 0.027)}px;
  line-height: 1.18;
}}
.row {{
  display: grid;
  grid-template-columns: 1.1fr 0.55fr 1fr 0.55fr;
  gap: {int(width * 0.018)}px;
  align-items: center;
  margin-top: {int(height * 0.018)}px;
  padding: {int(height * 0.018)}px {int(width * 0.024)}px;
  border-radius: {int(width * 0.018)}px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 {int(height * 0.005)}px {int(width * 0.020)}px rgba(15, 23, 42, 0.08);
  font-size: {int(width * 0.026)}px;
  font-weight: 800;
}}
.old {{ color: #9f2f2f; }}
.new {{ color: #0f7b55; }}
.saving {{
  margin-top: {int(height * 0.028)}px;
  border-radius: {int(width * 0.024)}px;
  padding: {int(height * 0.020)}px;
  background: #dcfce7;
  color: #06744f;
  text-align: center;
  font-size: {int(width * 0.066)}px;
  font-weight: 900;
}}
</style>
</head>
<body data-demo="{_safe_json(data)}">
  <div class="stage">
    <div class="desk"></div>
    <aside class="receipt">
      <h2>FRESH MART</h2>
      <div class="line"><span>BRAND CEREAL</span><strong>$8.49</strong></div>
      <div class="line"><span>SNACK PACKS</span><strong>$11.80</strong></div>
      <div class="line"><span>DRINKS</span><strong>$13.20</strong></div>
      <div class="line"><span>EXTRAS</span><strong>$6.51</strong></div>
      <div class="line"><span>LEAK FLAG</span><strong>{html.escape(savings)}</strong></div>
    </aside>
    <section class="phone">
      <div class="screen">
        <div class="bar">
          <span class="dot" style="background:#ef4444"></span>
          <span class="dot" style="background:#f59e0b"></span>
          <span class="dot" style="background:#22c55e"></span>
          <span>receipt-audit.local</span>
        </div>
        <div class="content">
          <div class="eyebrow">AI receipt audit</div>
          <div class="title">Cheaper swaps I would actually buy</div>
          <div class="prompt">{html.escape(prompt)}</div>
          <div id="rows"></div>
          <div class="saving">{html.escape(savings)}</div>
        </div>
      </div>
    </section>
  </div>
  <script>
    const data = JSON.parse(document.body.dataset.demo || '{{}}');
    const rows = document.getElementById('rows');
    (data.rows || []).forEach((row) => {{
      const node = document.createElement('div');
      node.className = 'row';
      node.innerHTML = `<span>${{row[0]}}</span><span class="old">${{row[1]}}</span><span class="new">${{row[2]}}</span><span class="new">${{row[3]}}</span>`;
      rows.appendChild(node);
    }});
  </script>
</body>
</html>
"""


def _savings_dashboard_html(scene: dict[str, Any], width: int, height: int) -> str:
    number = _clean_text(scene.get("number") or scene.get("payoff_number") or "$2,080")
    subline = _clean_text(scene.get("subline") or "possible yearly savings")
    data = {
        "number": number,
        "subline": subline,
        "items": ["$40/week leak", "AI swap list", "repeatable cart"],
    }
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={width}, initial-scale=1">
<title>Savings Dashboard Capture</title>
<style>
* {{ box-sizing: border-box; }}
html, body {{
  width: {width}px;
  height: {height}px;
  margin: 0;
  overflow: hidden;
  font-family: Arial, Helvetica, sans-serif;
  color: #102018;
  background:
    radial-gradient(circle at 82% 12%, rgba(46, 160, 112, 0.28), transparent 31%),
    radial-gradient(circle at 8% 75%, rgba(28, 88, 58, 0.20), transparent 32%),
    linear-gradient(180deg, #eef8f1 0%, #dcebe3 100%);
}}
.stage {{
  width: {width}px;
  height: {height}px;
  position: relative;
  padding: {int(height * 0.070)}px {int(width * 0.072)}px;
}}
.receipt {{
  position: absolute;
  width: {int(width * 0.34)}px;
  left: {int(width * 0.055)}px;
  bottom: {int(height * 0.115)}px;
  padding: {int(width * 0.030)}px;
  background: #fffdf2;
  border: 1px solid rgba(105, 92, 67, 0.18);
  box-shadow: 0 {int(height * 0.014)}px {int(width * 0.05)}px rgba(50, 42, 28, 0.22);
  transform: rotate(-5deg);
}}
.receipt h2 {{ margin: 0 0 {int(height * 0.015)}px; font-size: {int(width * 0.032)}px; }}
.rline {{
  display: flex;
  justify-content: space-between;
  border-bottom: 1px dashed rgba(83, 75, 59, 0.35);
  padding: {int(height * 0.007)}px 0;
  font-size: {int(width * 0.023)}px;
}}
.phone {{
  position: absolute;
  left: {int(width * 0.26)}px;
  top: {int(height * 0.055)}px;
  width: {int(width * 0.65)}px;
  height: {int(height * 0.82)}px;
  border-radius: {int(width * 0.060)}px;
  background: #0f172a;
  padding: {int(width * 0.026)}px;
  box-shadow: 0 {int(height * 0.025)}px {int(width * 0.09)}px rgba(15, 23, 42, 0.36);
}}
.screen {{
  height: 100%;
  border-radius: {int(width * 0.043)}px;
  overflow: hidden;
  background: linear-gradient(180deg, #f8fffb 0%, #eef8f1 100%);
}}
.top {{
  padding: {int(height * 0.035)}px {int(width * 0.044)}px {int(height * 0.015)}px;
  background: #113827;
  color: #e8fff3;
}}
.eyebrow {{ font-size: {int(width * 0.025)}px; font-weight: 800; color: #a9f7c8; text-transform: uppercase; }}
.title {{ margin-top: {int(height * 0.010)}px; font-size: {int(width * 0.052)}px; line-height: 1.04; font-weight: 900; }}
.body {{ padding: {int(height * 0.035)}px {int(width * 0.042)}px; }}
.number {{
  margin-top: {int(height * 0.014)}px;
  padding: {int(height * 0.030)}px {int(width * 0.020)}px;
  border-radius: {int(width * 0.030)}px;
  background: #dcfce7;
  color: #06744f;
  text-align: center;
  font-size: {int(width * 0.105)}px;
  font-weight: 900;
  box-shadow: inset 0 0 0 1px rgba(22, 163, 74, 0.20);
}}
.subline {{ margin-top: {int(height * 0.010)}px; text-align: center; color: #1f6a4f; font-size: {int(width * 0.034)}px; font-weight: 800; }}
.card {{
  margin-top: {int(height * 0.025)}px;
  padding: {int(height * 0.018)}px {int(width * 0.030)}px;
  border-radius: {int(width * 0.022)}px;
  background: #ffffff;
  border: 1px solid #d6eadf;
  box-shadow: 0 {int(height * 0.006)}px {int(width * 0.020)}px rgba(17, 56, 39, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: {int(width * 0.033)}px;
  font-weight: 800;
}}
.check {{ color: #08875d; font-size: {int(width * 0.040)}px; }}
.footer {{
  margin-top: {int(height * 0.030)}px;
  border-radius: {int(width * 0.025)}px;
  padding: {int(height * 0.022)}px;
  background: #123c2b;
  color: #e8fff3;
  font-size: {int(width * 0.034)}px;
  font-weight: 800;
  text-align: center;
}}
</style>
</head>
<body data-demo="{_safe_json(data)}">
  <div class="stage">
    <aside class="receipt">
      <h2>RECEIPT AUDIT</h2>
      <div class="rline"><span>EXTRAS</span><strong>$18</strong></div>
      <div class="rline"><span>BRAND SWAPS</span><strong>$13</strong></div>
      <div class="rline"><span>SNACKS</span><strong>$9</strong></div>
      <div class="rline"><span>WEEKLY LEAK</span><strong>$40</strong></div>
    </aside>
    <section class="phone">
      <div class="screen">
        <div class="top">
          <div class="eyebrow">AI savings result</div>
          <div class="title">One receipt audit found the leak</div>
        </div>
        <div class="body">
          <div class="number">{html.escape(number)}</div>
          <div class="subline">{html.escape(subline)}</div>
          <div id="cards"></div>
          <div class="footer">$2,080/year saved from one boring receipt audit</div>
        </div>
      </div>
    </section>
  </div>
  <script>
    const data = JSON.parse(document.body.dataset.demo || '{{}}');
    const cards = document.getElementById('cards');
    (data.items || []).forEach((item) => {{
      const node = document.createElement('div');
      node.className = 'card';
      node.innerHTML = `<span>${{item}}</span><span class="check">✓</span>`;
      cards.appendChild(node);
    }});
  </script>
</body>
</html>
"""


async def _capture_html_to_png(html_text: str, output_path: Path, width: int, height: int) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                f"--window-size={width},{height}",
            ],
        )
        page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        await page.set_content(html_text, wait_until="networkidle")
        await page.screenshot(path=str(output_path), full_page=False)
        await browser.close()


def resolve_hmr_playwright_capture(
    scene: dict[str, Any],
    capture_hint: str,
    output_dir: str | Path,
    width: int,
    height: int,
) -> dict[str, Any]:
    """Resolve an HMR Playwright screenshot asset or report why it failed."""
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    html_builders = {
        "receipt_audit_comparison": _receipt_audit_html,
        "savings_dashboard": _savings_dashboard_html,
    }
    html_builder = html_builders.get(capture_hint)
    if html_builder is None:
        return {
            "resolved_asset_type": None,
            "resolved_asset_path": None,
            "resolved_asset_provider": None,
            "asset_resolution_status": "unsupported_capture_hint",
            "fallback_used": True,
        }

    html_text = html_builder(scene, width, height)
    digest_seed = json.dumps(scene, sort_keys=True, default=str) + f":{width}x{height}:{capture_hint}"
    digest = hashlib.sha256(digest_seed.encode("utf-8")).hexdigest()[:16]
    html_path = output_root / f"hmr_{capture_hint}_{digest}.html"
    png_path = output_root / f"hmr_{capture_hint}_{digest}.png"
    html_path.write_text(html_text, encoding="utf-8")

    try:
        asyncio.run(_capture_html_to_png(html_text, png_path, width, height))
    except ImportError as exc:
        return {
            "resolved_asset_type": None,
            "resolved_asset_path": None,
            "resolved_asset_provider": None,
            "asset_resolution_status": f"playwright_unavailable:{exc}",
            "fallback_used": True,
            "html_fallback_path": str(html_path),
        }
    except Exception as exc:
        return {
            "resolved_asset_type": None,
            "resolved_asset_path": None,
            "resolved_asset_provider": None,
            "asset_resolution_status": f"playwright_capture_failed:{str(exc)[:120]}",
            "fallback_used": True,
            "html_fallback_path": str(html_path),
        }

    if not png_path.exists() or png_path.stat().st_size < 1000:
        return {
            "resolved_asset_type": None,
            "resolved_asset_path": None,
            "resolved_asset_provider": None,
            "asset_resolution_status": "playwright_capture_empty",
            "fallback_used": True,
            "html_fallback_path": str(html_path),
        }

    return {
        "resolved_asset_type": "playwright_capture",
        "resolved_asset_path": str(png_path),
        "resolved_asset_provider": "local_playwright_html",
        "asset_resolution_status": "resolved",
        "fallback_used": False,
        "html_fallback_path": str(html_path),
    }
