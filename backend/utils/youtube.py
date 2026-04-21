import re
import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:youtube\.com\/watch\?(?:.*&)?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)',
        r'youtube\.com\/shorts\/([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1).split('&')[0].split('?')[0]
    return None


def is_youtube_url(url: str) -> bool:
    return 'youtube.com' in url or 'youtu.be' in url


async def get_video_metadata(url: str) -> dict | None:
    """
    Fetch video title, channel and thumbnail via YouTube oembed (no API key required).
    Returns None on any failure — metadata is optional, never blocking.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None
    try:
        oembed_url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json'
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(oembed_url)
            if r.status_code != 200:
                return None
            data = r.json()
            meta = {
                'video_id': video_id,
                'title': data.get('title', ''),
                'channel': data.get('author_name', ''),
                'thumbnail_url': data.get('thumbnail_url', f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'),
            }
            print(f"[YouTube] \"{meta['title']}\" by {meta['channel']}")
            return meta
    except Exception as e:
        print(f"[YouTube] Metadata fetch failed (non-blocking): {e}")
        return None


def clean_video_transcript(text: str) -> str:
    """Remove filler words, repeated words, and transcription artifacts."""
    original_count = len(text.split())

    fillers = [
        r'\bum+\b', r'\buh+\b', r'\blike\b', r'\byou know\b', r'\bI mean\b',
        r'\bbasically\b', r'\bactually\b', r'\bliterally\b', r'\bkind of\b',
        r'\bsort of\b', r'\bright\??\b', r'\bokay\b', r'\bso+\b', r'\bwell\b',
        r'\bjust\b',
    ]
    for pattern in fillers:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove immediately repeated words (e.g. "really really" → "really")
    words = text.split()
    deduped = [w for i, w in enumerate(words) if i == 0 or w.lower() != words[i - 1].lower()]
    text = ' '.join(deduped)

    # Fix punctuation artifacts and whitespace
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r'\,\,+', ',', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace(' ,', ',').replace(' .', '.').strip()

    # Drop very short non-word fragments (transcription noise)
    text = ' '.join(w for w in text.split() if len(w) >= 3 or w in ('I', 'a', '.', ',', '!', '?'))

    cleaned_count = len(text.split())
    print(f"[YouTube] Cleaned: {original_count} → {cleaned_count} words ({original_count - cleaned_count} removed)")
    return text


def get_youtube_transcript(url: str, max_words: int = 4000) -> tuple[str | None, str | None]:
    """
    Fetch transcript from a YouTube URL.
    Returns (transcript_text, error_message) — one of them will be None.
    """
    print(f"\n[YouTube] Processing: {url}")

    video_id = extract_video_id(url)
    if not video_id:
        return None, "Invalid YouTube URL — could not extract video ID."

    print(f"[YouTube] Video ID: {video_id}")

    try:
        fetched = YouTubeTranscriptApi().fetch(
            video_id,
            languages=['en', 'en-US', 'en-GB'],
        )

        full_text = ' '.join(snippet.text for snippet in fetched)
        # Basic cleanup
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        # Remove filler words and transcription artifacts
        full_text = clean_video_transcript(full_text)

        words = full_text.split()
        print(f"[YouTube] Transcript: {len(words)} words")

        if len(words) > max_words:
            print(f"[YouTube] Truncating to {max_words} words")
            full_text = ' '.join(words[:max_words]) + ' [...transcript truncated]'

        print(f"[YouTube] Done — {len(full_text.split())} words returned")
        return full_text, None

    except TranscriptsDisabled:
        msg = "Transcripts are disabled for this video."
        print(f"[YouTube] {msg}")
        return None, msg

    except NoTranscriptFound:
        msg = "No English transcript found for this video. The creator may not have enabled captions."
        print(f"[YouTube] {msg}")
        return None, msg

    except VideoUnavailable:
        msg = "This video is unavailable or private."
        print(f"[YouTube] {msg}")
        return None, msg

    except Exception as e:
        msg = f"Could not retrieve transcript: {str(e)}"
        print(f"[YouTube] {msg}")
        return None, msg
