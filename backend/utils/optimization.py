import csv
import json
from pathlib import Path
from typing import Dict, List

METRICS_PATH = Path(__file__).resolve().parents[1] / "generated_videos" / "metrics.json"


def _load_metrics() -> List[Dict[str, object]]:
    if not METRICS_PATH.exists():
        return []
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_metrics(rows: List[Dict[str, object]]):
    METRICS_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def ingest_metrics_csv(csv_text: str) -> Dict[str, object]:
    if not csv_text.strip():
        raise ValueError("CSV text is empty.")

    reader = csv.DictReader(csv_text.splitlines())
    rows = [row for row in reader if row]
    if not rows:
        raise ValueError("No rows found in CSV.")

    existing = _load_metrics()
    combined = existing + rows
    _save_metrics(combined)
    return {"count": len(rows), "total": len(combined)}


def summarize_metrics() -> Dict[str, object]:
    rows = _load_metrics()
    if not rows:
        return {"total": 0, "top_hooks": []}

    scored = []
    for row in rows:
        hook = (row.get("hook") or row.get("title") or "").strip()
        retention = float(row.get("retention", 0) or 0)
        ctr = float(row.get("ctr", 0) or 0)
        score = retention * 0.7 + ctr * 0.3
        if hook:
            scored.append({"hook": hook, "score": round(score, 2)})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return {
        "total": len(rows),
        "top_hooks": scored[:10],
    }
