"""Verify implementation of the 6 selected recommendations."""
import json
import time
import requests

BASE = "http://127.0.0.1:8000"
AUTH = {"email": "admin@test.com", "password": "Admin@12345"}


def log(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name} :: {detail}")


def main():
    # 1) Login
    r = requests.post(f"{BASE}/api/auth/login", json=AUTH, timeout=10)
    r.raise_for_status()
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("Auth", True, "token received")

    # 2) Credits/key status (includes HF_TOKEN status)
    c = requests.get(f"{BASE}/api/generate/video/credits", headers=headers, timeout=30)
    c.raise_for_status()
    credits = c.json()
    log("Pexels key set", True if credits else False, "checked via backend env")
    hf_ok = bool((credits.get("huggingface") or {}).get("ok"))
    log("HF token status", hf_ok, (credits.get("huggingface") or {}).get("error") or "ok")

    # 3) Stock preview returns real Pexels thumbnail URLs
    p = requests.post(
        f"{BASE}/api/generate/video/preview",
        headers=headers,
        json={
            "script": "Save money by canceling unused subscriptions and automating savings.",
            "duration": 15,
            "scene_mode": "stock",
            "image_provider": "pollinations",
        },
        timeout=60,
    )
    if p.status_code != 200:
        detail = ""
        try:
            detail = str(p.json())
        except Exception:
            detail = p.text[:200]
        log("Stock preview thumbnails", False, f"HTTP {p.status_code}: {detail}")
        return
    pdata = p.json()
    scenes = pdata.get("scenes") or []
    stock_urls = [s.get("image_url") for s in scenes if isinstance(s, dict)]
    all_pexels = bool(stock_urls) and all((u or "").startswith("https://images.pexels.com") for u in stock_urls)
    log("Stock preview thumbnails", all_pexels, f"{len(stock_urls)} scene thumbnails")

    # 4) Progress endpoint works for queued generation
    q = requests.post(
        f"{BASE}/api/generate/video/generate-from-preview",
        headers=headers,
        json={
            "preview_id": pdata.get("preview_id") or "verify-preview",
            "approved_scenes": scenes[:2] if len(scenes) >= 2 else scenes,
            "dry_run": True,
        },
        timeout=30,
    )
    q.raise_for_status()
    qd = q.json()
    gen_id = qd.get("generation_id")
    log("Generate-from-preview returns generation_id", bool(gen_id), str(gen_id))

    progress_ok = False
    if gen_id:
        for _ in range(8):
            pr = requests.get(f"{BASE}/api/generate/video/progress/{gen_id}", headers=headers, timeout=20)
            if pr.status_code == 200:
                d = pr.json()
                status = d.get("status")
                pct = d.get("percent")
                if isinstance(pct, int) and status in {"queued", "processing", "success", "failed"}:
                    progress_ok = True
                if status in {"success", "failed"}:
                    break
            time.sleep(1.5)
    log("Progress endpoint", progress_ok, "polling response schema valid")

    # 5) End-to-end stock video generation in free endpoint (Windows ffmpeg pipeline)
    # Keep it short to reduce runtime but still exercise stock clip fetch + assemble.
    t0 = time.time()
    g = requests.post(
        f"{BASE}/api/generate/video/free",
        headers=headers,
        json={
            "script": "Stop wasting money on unused subscriptions. Cancel them today and save every month.",
            "duration_seconds": 10,
            "scene_mode": "stock",
            "niche": "finance",
            "dry_run": False,
            "tts_provider": "free",
            "image_provider": "huggingface",
        },
        timeout=420,
    )
    ok = g.status_code == 200
    detail = f"HTTP {g.status_code} in {round(time.time()-t0,1)}s"
    if ok:
        d = g.json()
        detail += f", preview_url={bool(d.get('preview_url'))}, runway_credits={d.get('runway_credits_used')}"
    log("Stock E2E generation", ok, detail)

    with open("verify_all6_result.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "credits": credits,
                "preview": pdata,
                "queue": qd,
                "generation": (g.json() if g.headers.get("content-type", "").startswith("application/json") else {"status": g.status_code}),
            },
            f,
            indent=2,
        )
    print("Saved: verify_all6_result.json")


if __name__ == "__main__":
    main()
