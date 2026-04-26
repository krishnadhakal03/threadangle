# Day6 Productization Opportunities

Day6 exposed repeatable production needs that should become product features instead of per-video custom code.

## Immediate reusable improvement

Proof Clip Injection / Scene Replace should be productized first.

MVP:
- Add a scene asset map that accepts `image`, `video`, or `browser_capture` assets per scene.
- Store lock metadata: `replaceable`, `duration_locked`, `privacy_reviewed`, and `source_label`.
- Render a proof insert before a reconstructed or templated scene without claiming the reconstruction is live capture.

Why now:
- Day6 needed a real Google AI Mode screenshot plus a local reenactment.
- This pattern will repeat for receipts, statements, dashboards, and browser proof clips.

Story-first v3 adds three helper patterns worth keeping reusable:
- Proof screenshot magnifier: crop a wide proof screenshot into a vertical documentary background, then place a readable excerpt card over it.
- Before/after replacement math card: show old cost rows and replacement rows as comparable structured proof, not as decorative text.
- Receipt documentary motion helper: apply tiny handheld drift, pan, and tap-like crop changes to static screenshots so they feel like app usage.

## Backlog candidates

Real Browser Proof Template:
- Generalize Day4 browser capture into reusable templates for search, AI response, scroll-to-sources, and proof-frame export.
- Add explicit failure states for captcha, sign-in required, provider unavailable, and blocked page.

Hook Engine:
- Template first-two-second hooks with swappable proof assets, amount overlays, and locked caption-safe zones.
- Use the same hook shell for ride cost, bill audit, grocery receipt, and subscription proof videos.

Real Browser Provider Routing:
- Define provider order as data: Google AI, ChatGPT/Claude, user proof insert, local DOM reconstruction.
- Require visible provider labeling when the scene is reconstructed rather than live-captured.

## Productize now or later

Productize Proof Clip Injection now.

Defer full Real Browser Provider Routing until at least two more proof videos need live capture across different providers.
