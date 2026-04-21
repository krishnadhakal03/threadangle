from typing import List, Dict


def build_word_timestamps(text: str, duration_seconds: float) -> List[Dict[str, float]]:
    words = [w for w in (text or "").split() if w]
    if not words:
        return []

    total = max(1.0, float(duration_seconds or 1))
    step = total / len(words)
    out = []
    t = 0.0
    for word in words:
        start = t
        end = min(total, t + step)
        out.append({"word": word, "start": round(start, 3), "end": round(end, 3)})
        t += step
    return out


def build_srt_from_words(words: List[Dict[str, float]]) -> str:
    if not words:
        return ""

    def fmt(sec: float) -> str:
        sec = max(0.0, float(sec))
        h = int(sec // 3600)
        sec %= 3600
        m = int(sec // 60)
        sec %= 60
        s = int(sec)
        ms = int(round((sec - s) * 1000))
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    lines = []
    for i, item in enumerate(words, start=1):
        lines.append(str(i))
        lines.append(f"{fmt(item['start'])} --> {fmt(item['end'])}")
        lines.append(item["word"])
        lines.append("")
    return "\n".join(lines)
