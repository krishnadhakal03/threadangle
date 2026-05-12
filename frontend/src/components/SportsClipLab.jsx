import React, { useMemo, useState } from 'react';
import { api } from '../utils/api';

const DURATIONS = ['15s', '20s', '30s'];
const SPORTS = ['NBA', 'EPL', 'NFL', 'Soccer', 'Other'];
const PLATFORMS = ['All', 'YouTube Shorts', 'TikTok', 'Reels'];
const TONES = ['cinematic', 'hype', 'emotional', 'rivalry', 'underdog', 'breaking-news'];
const IMAGE_PROVIDERS = [
  { value: 'huggingface', label: 'HuggingFace / fallback' },
  { value: 'pollinations', label: 'Pollinations' },
];

const EXAMPLES = {
  nba: {
    label: 'NBA hot game today',
    eventTopic: 'Spurs vs Timberwolves Game 5, May 12, 2026',
    sport: 'NBA',
    teamsPlayers: 'San Antonio Spurs, Minnesota Timberwolves, Victor Wembanyama, Anthony Edwards',
    targetPlatform: 'All',
    duration: '20s',
    tone: 'hype',
    hook: 'Wemby is back under playoff pressure tonight.',
    body: 'Game 5 is tied 2-2, the stage is in San Antonio, and one run could swing the whole series.',
    cta: 'Who owns Game 5: Wemby or Ant?',
  },
  city: {
    label: 'Manchester City game tomorrow',
    eventTopic: 'Manchester City vs Crystal Palace, May 13, 2026',
    sport: 'EPL',
    teamsPlayers: 'Manchester City, Crystal Palace, Erling Haaland, Phil Foden, Eberechi Eze',
    targetPlatform: 'All',
    duration: '20s',
    tone: 'cinematic',
    hook: 'City cannot blink in the title race tomorrow.',
    body: 'Crystal Palace arrive at the Etihad with spoiler energy while City chase every point under pressure.',
    cta: 'Will City handle the pressure or slip?',
  },
};

const INITIAL_FORM = EXAMPLES.nba;

const ButtonIcon = ({ type }) => {
  const paths = {
    play: 'M5 3l14 9-14 9V3z',
    copy: 'M8 7V5a2 2 0 012-2h7a2 2 0 012 2v9a2 2 0 01-2 2h-2M6 7h7a2 2 0 012 2v9a2 2 0 01-2 2H6a2 2 0 01-2-2V9a2 2 0 012-2z',
    code: 'M8 9l-4 3 4 3m8-6l4 3-4 3M14 4l-4 16',
    tag: 'M7 7h.01M3 11V5a2 2 0 012-2h6l10 10a2 2 0 010 2.83L15.83 21a2 2 0 01-2.83 0L3 11z',
  };

  return (
    <svg className="w-4 h-4" fill={type === 'play' ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={paths[type]} />
    </svg>
  );
};

function CopyButton({ text, children, className = '' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={`inline-flex items-center justify-center gap-2 rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white ${className}`}
    >
      <ButtonIcon type="copy" />
      {copied ? 'Copied' : children}
    </button>
  );
}

function splitText(text) {
  return text
    .split(/[\n.]+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function getSceneDurations(totalDuration, count) {
  const total = Number.parseInt(totalDuration, 10) || 20;
  const base = Math.floor(total / count);
  let remainder = total - base * count;
  return Array.from({ length: count }, () => {
    const next = base + (remainder > 0 ? 1 : 0);
    remainder -= 1;
    return next;
  });
}

function makeHashtags(form) {
  const topicTags = form.teamsPlayers
    .split(',')
    .map((item) => item.trim().replace(/[^a-zA-Z0-9]/g, ''))
    .filter(Boolean)
    .slice(0, 4)
    .map((item) => `#${item}`);

  const sportTag = `#${form.sport.replace(/[^a-zA-Z0-9]/g, '') || 'Sports'}`;
  return [...new Set(['#Sports', sportTag, '#Shorts', '#GameDay', ...topicTags])].slice(0, 8);
}

function buildScenes(form) {
  const total = Number.parseInt(form.duration, 10) || 20;
  const count = total <= 15 ? 4 : total >= 30 ? 6 : 5;
  const durations = getSceneDurations(form.duration, count);
  const bodyLines = splitText(form.body);
  const subject = form.teamsPlayers || form.eventTopic || 'the matchup';

  const beats = [
    {
      label: 'Cold open',
      caption: form.hook || `The pressure is on for ${form.eventTopic}.`,
      visual: 'a dramatic close-up with arena lights, tense faces, and rising crowd energy',
      motion: 'slow push-in, light camera shake, flashes from the crowd, high-contrast reveal',
      note: 'Open with the strongest image. Cut on the first beat drop.',
    },
    {
      label: 'Stakes',
      caption: bodyLines[0] || 'Everything changes after this matchup.',
      visual: 'a wide vertical scene showing the stadium, scoreboard glow, and players warming up',
      motion: 'vertical parallax move from crowd to court or pitch, quick scoreboard rack focus',
      note: 'Use a fast whoosh transition from scene 1.',
    },
    {
      label: 'Star focus',
      caption: `${subject.split(',')[0]?.trim() || 'The star'} has to set the tone.`,
      visual: 'a star player silhouette in generic team colors, sweat, tunnel smoke, no official logos',
      motion: 'hero walk-in, shallow depth of field, jersey fabric movement, lens flare sweep',
      note: 'Hold the player in center frame for caption readability.',
    },
    {
      label: 'Turning point',
      caption: bodyLines[1] || 'One moment can flip the entire story.',
      visual: 'a decisive sports action moment frozen at peak tension, defenders closing in, crowd blurred',
      motion: 'speed ramp into a freeze-frame, slight zoom, impact shake on the imagined play',
      note: 'Trim tightly. Keep only the most energetic 3 to 5 seconds.',
    },
    {
      label: 'Prediction',
      caption: form.cta || 'Who wins this one?',
      visual: 'split-screen rivalry poster with both sides facing off under bright arena lights',
      motion: 'split-screen slide together, sparks of light, final title card reveal',
      note: 'End with a clean CTA and leave half a second of breathing room.',
    },
    {
      label: 'Final punch',
      caption: form.cta || 'Drop your pick before tip-off.',
      visual: 'vertical social-ready final frame with empty lower third for comments and reactions',
      motion: 'quick zoom out to final frame, subtle crowd pulse, hard cut to black',
      note: 'Use this only for 30 second versions or if the story needs a stronger ending.',
    },
  ];

  return beats.slice(0, count).map((beat, index) => ({
    number: index + 1,
    label: beat.label,
    duration: durations[index],
    imagePrompt: [
      `Vertical 9:16 ${form.sport} short scene for "${form.eventTopic}".`,
      `Tone: ${form.tone}. Subject: ${subject}.`,
      `${beat.visual}.`,
      'Cinematic sports editorial style, realistic lighting, sharp subject, readable negative space for captions, no official logos, no watermarks, no broadcast graphics.',
    ].join(' '),
    videoPrompt: [
      `Animate this image as a ${durations[index]} second vertical sports clip.`,
      `${beat.motion}.`,
      'Keep faces and uniforms stable, avoid text artifacts, preserve 9:16 framing, leave lower third clear for captions.',
    ].join(' '),
    caption: beat.caption,
    editingNote: beat.note,
  }));
}

function buildVoiceover(form, scenes) {
  const lines = [
    form.hook,
    ...scenes.slice(1, -1).map((scene) => scene.caption),
    form.cta,
  ].filter(Boolean);

  return lines.join(' ');
}

function buildMetadata(form) {
  const hashtags = makeHashtags(form);
  const titleCore = form.eventTopic || 'Sports short';
  const question = form.cta || 'Who wins this one?';
  const shortTitle = `${titleCore}: pressure moment`;
  const caption = `${form.hook || titleCore} ${question}`;

  return {
    youtube: {
      title: shortTitle.slice(0, 70),
      description: `${form.body}\n\n${question}\n\nMade with a local-first Threadangle Sports Clip Lab workflow.\n${hashtags.join(' ')}`,
      hashtags: hashtags.join(' '),
    },
    tiktok: {
      caption: `${caption} ${hashtags.filter((tag) => tag !== '#Shorts').join(' ')}`,
      hashtags: hashtags.filter((tag) => tag !== '#Shorts').join(' '),
    },
    reels: {
      caption: `${caption}\n\n${hashtags.join(' ')}`,
      hashtags: hashtags.join(' '),
    },
    facebook: {
      caption: `${caption}\n\n${form.body}\n\n${hashtags.slice(0, 6).join(' ')}`,
      hashtags: hashtags.slice(0, 6).join(' '),
    },
  };
}

function buildPromptText(packageData) {
  return packageData.scenes.map((scene) => [
    `Scene ${scene.number}: ${scene.label}`,
    `Duration: ${scene.duration}s`,
    `Image prompt: ${scene.imagePrompt}`,
    `Image-to-video prompt: ${scene.videoPrompt}`,
    `Caption: ${scene.caption}`,
    `Editing note: ${scene.editingNote}`,
  ].join('\n')).join('\n\n');
}

function buildMetadataText(metadata) {
  return [
    `YouTube Shorts\nTitle: ${metadata.youtube.title}\nDescription:\n${metadata.youtube.description}\nHashtags: ${metadata.youtube.hashtags}`,
    `TikTok\nCaption: ${metadata.tiktok.caption}\nHashtags: ${metadata.tiktok.hashtags}`,
    `Instagram Reels\nCaption: ${metadata.reels.caption}\nHashtags: ${metadata.reels.hashtags}`,
    `Facebook Reels\nCaption: ${metadata.facebook.caption}\nHashtags: ${metadata.facebook.hashtags}`,
  ].join('\n\n');
}

function buildPackageText(packageData) {
  return [
    `Sports Scene Package: ${packageData.form.eventTopic}`,
    `Sport: ${packageData.form.sport}`,
    `Teams/players: ${packageData.form.teamsPlayers}`,
    `Duration: ${packageData.form.duration}`,
    `Tone: ${packageData.form.tone}`,
    '',
    buildPromptText(packageData),
    '',
    `Voiceover script:\n${packageData.voiceover}`,
    '',
    buildMetadataText(packageData.metadata),
  ].join('\n');
}

function buildWorkflowInstructions(scenes) {
  const imageNames = scenes.map((scene) => `scene${scene.number}.png`).join(', ');
  const clipNames = scenes.map((scene) => `scene${scene.number}.mp4`).join(', ');

  return [
    'Sports Clip Lab image-generated workflow',
    `1. Generate or download scene images from this page as: ${imageNames}.`,
    '2. Review each image before creating video clips. Regenerate any weak image first.',
    '3. Upload each image to Meta AI or your selected image-to-video tool.',
    `4. Use the matching image-to-video prompt for each scene and export clips as: ${clipNames}.`,
    '5. Upload the MP4 clips to Colab.',
    '6. Run the copied stitch script.',
    '7. Download final_vertical_short.mp4 and post with the generated metadata.',
  ].join('\n');
}

function buildColabScript(scenes) {
  const sceneData = scenes.map((scene) => ({
    file: `scene${scene.number}.mp4`,
    duration: scene.duration,
    caption: scene.caption,
  }));

  return `# Threadangle Sports Clip Lab: image-generated local/Colab stitch script
# No Runway, ElevenLabs, paid video APIs, or production rendering.
# Workflow:
# 1) Generate/download images as scene1.png, scene2.png, scene3.png...
# 2) Manually approve images, then create clips in Meta AI or another image-to-video tool.
# 3) Export clips as scene1.mp4, scene2.mp4, scene3.mp4...
# 4) Upload those MP4 clips here and run this stitch script.
!pip -q install moviepy==1.0.3 pillow imageio-ffmpeg

from google.colab import files
uploaded = files.upload()

import os
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, ImageClip, AudioFileClip

SCENES = ${JSON.stringify(sceneData, null, 2)}
TARGET_SIZE = (1080, 1920)
OUTPUT_FILE = "final_vertical_short.mp4"

def resize_vertical(clip):
    target_w, target_h = TARGET_SIZE
    scale = max(target_w / clip.w, target_h / clip.h)
    resized = clip.resize(scale)
    return resized.crop(
        x_center=resized.w / 2,
        y_center=resized.h / 2,
        width=target_w,
        height=target_h,
    )

def load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def make_caption_image(text):
    width, height = TARGET_SIZE
    img = Image.new("RGBA", TARGET_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(64)
    small = load_font(44)
    lines = textwrap.wrap(text.upper(), width=24)
    if len(lines) > 3:
        font = small
        lines = textwrap.wrap(text.upper(), width=30)[:4]

    line_heights = []
    line_widths = []
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        line_widths.append(box[2] - box[0])
        line_heights.append(box[3] - box[1])

    block_h = sum(line_heights) + max(0, len(lines) - 1) * 18
    y = int(height * 0.68)
    pad_x, pad_y = 44, 30
    box_w = min(width - 96, max(line_widths or [0]) + pad_x * 2)
    box_h = block_h + pad_y * 2
    box_x = (width - box_w) // 2
    draw.rounded_rectangle(
        [box_x, y - pad_y, box_x + box_w, y - pad_y + box_h],
        radius=28,
        fill=(0, 0, 0, 170),
    )

    cursor_y = y
    for line, line_h, line_w in zip(lines, line_heights, line_widths):
        x = (width - line_w) // 2
        draw.text(
            (x, cursor_y),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )
        cursor_y += line_h + 18

    return np.array(img)

clips = []
for scene in SCENES:
    filename = scene["file"]
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Missing {filename}. Upload clips as scene1.mp4, scene2.mp4, etc.")

    clip = VideoFileClip(filename)
    trim_to = min(float(scene["duration"]), clip.duration)
    clip = clip.subclip(0, trim_to)
    clip = resize_vertical(clip)

    caption = ImageClip(make_caption_image(scene["caption"])).set_duration(trim_to)
    composed = CompositeVideoClip([clip, caption], size=TARGET_SIZE).set_duration(trim_to)
    clips.append(composed)

final = concatenate_videoclips(clips, method="compose")

if os.path.exists("voiceover.mp3"):
    audio = AudioFileClip("voiceover.mp3").subclip(0, min(final.duration, AudioFileClip("voiceover.mp3").duration))
    final = final.set_audio(audio)
elif os.path.exists("music.mp3"):
    audio = AudioFileClip("music.mp3").volumex(0.15).subclip(0, min(final.duration, AudioFileClip("music.mp3").duration))
    final = final.set_audio(audio)

final.write_videofile(
    OUTPUT_FILE,
    fps=30,
    codec="libx264",
    audio_codec="aac",
    preset="medium",
    threads=2,
)

files.download(OUTPUT_FILE)
`;
}

const CRC_TABLE = Array.from({ length: 256 }, (_, index) => {
  let value = index;
  for (let bit = 0; bit < 8; bit += 1) {
    value = (value & 1) ? (0xEDB88320 ^ (value >>> 1)) : (value >>> 1);
  }
  return value >>> 0;
});

function crc32(bytes) {
  let crc = 0xFFFFFFFF;
  for (let index = 0; index < bytes.length; index += 1) {
    crc = CRC_TABLE[(crc ^ bytes[index]) & 0xFF] ^ (crc >>> 8);
  }
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

function writeUint16(bytes, value) {
  bytes.push(value & 0xFF, (value >>> 8) & 0xFF);
}

function writeUint32(bytes, value) {
  bytes.push(value & 0xFF, (value >>> 8) & 0xFF, (value >>> 16) & 0xFF, (value >>> 24) & 0xFF);
}

function stringToBytes(value) {
  return Array.from(new TextEncoder().encode(value));
}

function dataUrlToBytes(dataUrl) {
  const [, base64 = ''] = String(dataUrl || '').split(',');
  const binary = window.atob(base64);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function createZip(files) {
  const output = [];
  const centralDirectory = [];
  let offset = 0;

  files.forEach((file) => {
    const nameBytes = stringToBytes(file.name);
    const data = file.bytes;
    const checksum = crc32(data);

    const localHeader = [];
    writeUint32(localHeader, 0x04034B50);
    writeUint16(localHeader, 20);
    writeUint16(localHeader, 0);
    writeUint16(localHeader, 0);
    writeUint16(localHeader, 0);
    writeUint16(localHeader, 0);
    writeUint32(localHeader, checksum);
    writeUint32(localHeader, data.length);
    writeUint32(localHeader, data.length);
    writeUint16(localHeader, nameBytes.length);
    writeUint16(localHeader, 0);
    localHeader.push(...nameBytes);
    output.push(...localHeader, ...data);

    const directoryHeader = [];
    writeUint32(directoryHeader, 0x02014B50);
    writeUint16(directoryHeader, 20);
    writeUint16(directoryHeader, 20);
    writeUint16(directoryHeader, 0);
    writeUint16(directoryHeader, 0);
    writeUint16(directoryHeader, 0);
    writeUint16(directoryHeader, 0);
    writeUint32(directoryHeader, checksum);
    writeUint32(directoryHeader, data.length);
    writeUint32(directoryHeader, data.length);
    writeUint16(directoryHeader, nameBytes.length);
    writeUint16(directoryHeader, 0);
    writeUint16(directoryHeader, 0);
    writeUint16(directoryHeader, 0);
    writeUint16(directoryHeader, 0);
    writeUint32(directoryHeader, 0);
    writeUint32(directoryHeader, offset);
    directoryHeader.push(...nameBytes);
    centralDirectory.push(...directoryHeader);

    offset += localHeader.length + data.length;
  });

  const centralOffset = output.length;
  output.push(...centralDirectory);

  writeUint32(output, 0x06054B50);
  writeUint16(output, 0);
  writeUint16(output, 0);
  writeUint16(output, files.length);
  writeUint16(output, files.length);
  writeUint32(output, centralDirectory.length);
  writeUint32(output, centralOffset);
  writeUint16(output, 0);

  return new Blob([new Uint8Array(output)], { type: 'application/zip' });
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-[#8B949E]">{label}</span>
      {children}
    </label>
  );
}

function TextInput(props) {
  return (
    <input
      {...props}
      className="w-full rounded-lg border border-[#30363D] bg-[#0D1117] px-3 py-2.5 text-sm text-[#E6EDF3] outline-none transition-colors placeholder:text-[#484F58] focus:border-[#58A6FF]"
    />
  );
}

function TextArea(props) {
  return (
    <textarea
      {...props}
      className="w-full rounded-lg border border-[#30363D] bg-[#0D1117] px-3 py-2.5 text-sm text-[#E6EDF3] outline-none transition-colors placeholder:text-[#484F58] focus:border-[#58A6FF]"
    />
  );
}

function Select({ children, ...props }) {
  return (
    <select
      {...props}
      className="w-full rounded-lg border border-[#30363D] bg-[#0D1117] px-3 py-2.5 text-sm text-[#E6EDF3] outline-none transition-colors focus:border-[#58A6FF]"
    >
      {children}
    </select>
  );
}

export default function SportsClipLab() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [generatedForm, setGeneratedForm] = useState(INITIAL_FORM);
  const [imageProvider, setImageProvider] = useState('huggingface');
  const [sceneImages, setSceneImages] = useState({});
  const [generatingAll, setGeneratingAll] = useState(false);
  const [activeScene, setActiveScene] = useState(null);
  const [imageBatchMessage, setImageBatchMessage] = useState(null);

  const packageData = useMemo(() => {
    const scenes = buildScenes(generatedForm);
    const metadata = buildMetadata(generatedForm);
    return {
      form: generatedForm,
      scenes,
      metadata,
      voiceover: buildVoiceover(generatedForm, scenes),
    };
  }, [generatedForm]);

  const colabScript = useMemo(() => buildColabScript(packageData.scenes), [packageData.scenes]);
  const promptText = useMemo(() => buildPromptText(packageData), [packageData]);
  const metadataText = useMemo(() => buildMetadataText(packageData.metadata), [packageData.metadata]);
  const packageText = useMemo(() => buildPackageText(packageData), [packageData]);
  const workflowInstructions = useMemo(() => buildWorkflowInstructions(packageData.scenes), [packageData.scenes]);
  const generatedImageCount = Object.values(sceneImages).filter((image) => image?.status === 'success' && image.imageUrl).length;

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const generatePackage = () => {
    setGeneratedForm({ ...form });
    setSceneImages({});
    setImageBatchMessage(null);
  };

  const generateSceneImage = async (scene, forceVariation = false) => {
    const sceneKey = scene.number;
    setActiveScene(sceneKey);
    setSceneImages((current) => ({
      ...current,
      [sceneKey]: {
        ...current[sceneKey],
        status: 'generating',
        error: null,
      },
    }));

    try {
      const data = await api.regenerateSceneImage({
        scene_index: scene.number - 1,
        scene_description: scene.imagePrompt,
        character_profile: {
          type: `${packageData.form.sport} sports scene`,
          style: 'cinematic sports editorial',
          event: packageData.form.eventTopic,
          teams_players: packageData.form.teamsPlayers,
        },
        image_provider: imageProvider,
        variation_token: forceVariation ? `${Date.now()}-${scene.number}` : undefined,
      });

      if (!data?.image_url) {
        throw new Error('Image not generated by provider.');
      }

      setSceneImages((current) => ({
        ...current,
        [sceneKey]: {
          status: 'success',
          imageUrl: data.image_url,
          provider: data.provider || imageProvider,
          promptUsed: data.prompt_used || scene.imagePrompt,
          filename: `scene${scene.number}.png`,
          error: null,
        },
      }));
      return { ok: true, scene: sceneKey };
    } catch (err) {
      const message = err?.message || 'Provider failed or image API is missing.';
      setSceneImages((current) => ({
        ...current,
        [sceneKey]: {
          ...current[sceneKey],
          status: 'error',
          error: message,
          filename: `scene${scene.number}.png`,
        },
      }));
      return { ok: false, scene: sceneKey, error: message };
    } finally {
      setActiveScene(null);
    }
  };

  const generateAllSceneImages = async () => {
    setGeneratingAll(true);
    setImageBatchMessage(null);

    const results = [];
    for (const scene of packageData.scenes) {
      const result = await generateSceneImage(scene, false);
      results.push(result);
    }

    const failures = results.filter((result) => !result.ok);
    if (failures.length === 0) {
      setImageBatchMessage({ type: 'success', text: `Generated ${results.length} scene images.` });
    } else if (failures.length === results.length) {
      setImageBatchMessage({ type: 'error', text: 'Image API missing or provider failed for every scene. The scene package is still available.' });
    } else {
      setImageBatchMessage({ type: 'warning', text: `Generated ${results.length - failures.length} of ${results.length} images. Regenerate failed scenes individually.` });
    }
    setGeneratingAll(false);
  };

  const downloadSceneImagesZip = () => {
    const files = packageData.scenes
      .map((scene) => sceneImages[scene.number])
      .filter((image) => image?.status === 'success' && image.imageUrl)
      .map((image) => ({
        name: image.filename,
        bytes: dataUrlToBytes(image.imageUrl),
      }));

    if (!files.length) {
      setImageBatchMessage({ type: 'error', text: 'No generated images are ready to download.' });
      return;
    }

    downloadBlob(createZip(files), 'threadangle-sports-scenes.zip');
  };

  return (
    <div className="min-h-screen bg-[#09090B] px-4 py-6 text-[#E6EDF3] md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 border-b border-[#21262D] pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-[#58A6FF]">Local / Colab only</p>
            <h1 className="mt-2 text-2xl font-bold text-white md:text-3xl">Sports Clip Lab</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-[#8B949E]">
              Build scene prompts, manual clip instructions, a Colab stitch script, and posting metadata without calling paid render or voice APIs.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(EXAMPLES).map(([key, example]) => (
              <button
                key={key}
                type="button"
                onClick={() => {
                  setForm(example);
                  setGeneratedForm(example);
                }}
                className="rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white"
              >
                {example.label}
              </button>
            ))}
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[420px_1fr]">
          <div className="space-y-4 rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              <Field label="Event/topic">
                <TextInput value={form.eventTopic} onChange={(e) => updateField('eventTopic', e.target.value)} placeholder="Spurs vs Timberwolves Game 5" />
              </Field>
              <Field label="Sport">
                <Select value={form.sport} onChange={(e) => updateField('sport', e.target.value)}>
                  {SPORTS.map((sport) => <option key={sport}>{sport}</option>)}
                </Select>
              </Field>
              <Field label="Teams/players">
                <TextArea rows={3} value={form.teamsPlayers} onChange={(e) => updateField('teamsPlayers', e.target.value)} placeholder="Teams, players, rivalry angle" />
              </Field>
              <Field label="Target platform">
                <Select value={form.targetPlatform} onChange={(e) => updateField('targetPlatform', e.target.value)}>
                  {PLATFORMS.map((platform) => <option key={platform}>{platform}</option>)}
                </Select>
              </Field>
              <Field label="Duration">
                <Select value={form.duration} onChange={(e) => updateField('duration', e.target.value)}>
                  {DURATIONS.map((duration) => <option key={duration}>{duration}</option>)}
                </Select>
              </Field>
              <Field label="Tone">
                <Select value={form.tone} onChange={(e) => updateField('tone', e.target.value)}>
                  {TONES.map((tone) => <option key={tone}>{tone}</option>)}
                </Select>
              </Field>
              <Field label="Image provider">
                <Select value={imageProvider} onChange={(e) => setImageProvider(e.target.value)}>
                  {IMAGE_PROVIDERS.map((provider) => <option key={provider.value} value={provider.value}>{provider.label}</option>)}
                </Select>
                <p className="mt-1.5 text-[11px] leading-4 text-[#8B949E]">Uses the existing Threadangle image endpoint only. No Runway, ElevenLabs, or video render APIs are called.</p>
              </Field>
              <Field label="Hook">
                <TextArea rows={2} value={form.hook} onChange={(e) => updateField('hook', e.target.value)} />
              </Field>
              <Field label="Body">
                <TextArea rows={4} value={form.body} onChange={(e) => updateField('body', e.target.value)} />
              </Field>
              <Field label="CTA">
                <TextInput value={form.cta} onChange={(e) => updateField('cta', e.target.value)} />
              </Field>
            </div>

            <button
              type="button"
              onClick={generatePackage}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#238636] px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-[#2EA043]"
            >
              <ButtonIcon type="play" />
              Generate Sports Scene Package
            </button>

            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
              <button
                type="button"
                onClick={generateAllSceneImages}
                disabled={generatingAll}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#1F6FEB] px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-[#388BFD] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <ButtonIcon type="play" />
                {generatingAll ? `Generating${activeScene ? ` Scene ${activeScene}` : ''}...` : 'Generate Scene Images'}
              </button>
              <button
                type="button"
                onClick={downloadSceneImagesZip}
                disabled={generatedImageCount === 0}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#30363D] bg-[#161B22] px-4 py-3 text-sm font-bold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                Download Images ZIP
              </button>
            </div>

            {imageBatchMessage && (
              <div className={`rounded-lg border px-3 py-2 text-xs leading-5 ${
                imageBatchMessage.type === 'success'
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                  : imageBatchMessage.type === 'warning'
                    ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                    : 'border-red-500/30 bg-red-500/10 text-red-300'
              }`}>
                {imageBatchMessage.text}
              </div>
            )}

            <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-1">
              <CopyButton text={promptText}>Copy All Scene Prompts</CopyButton>
              <CopyButton text={colabScript}><ButtonIcon type="code" />Copy Colab Script</CopyButton>
              <CopyButton text={metadataText}><ButtonIcon type="tag" />Copy Platform Metadata</CopyButton>
            </div>
          </div>

          <div className="space-y-6">
            <section>
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-white">Scene Package</h2>
                  <p className="text-xs text-[#8B949E]">{packageData.scenes.length} scenes for {packageData.form.duration}</p>
                </div>
                <CopyButton text={packageText}>Copy Full Package</CopyButton>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                {packageData.scenes.map((scene) => (
                  <article key={scene.number} className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <div>
                        <h3 className="font-bold text-white">Scene {scene.number}: {scene.label}</h3>
                        <p className="text-xs text-[#8B949E]">{scene.duration}s · scene{scene.number}.png</p>
                      </div>
                      <div className="flex shrink-0 flex-wrap justify-end gap-2">
                        <CopyButton text={scene.videoPrompt}>Copy I2V Prompt</CopyButton>
                        <button
                          type="button"
                          onClick={() => generateSceneImage(scene, true)}
                          disabled={sceneImages[scene.number]?.status === 'generating'}
                          className="inline-flex items-center justify-center rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {sceneImages[scene.number]?.status === 'generating' ? 'Generating' : 'Regenerate Image'}
                        </button>
                      </div>
                    </div>
                    <div className="space-y-3 text-sm">
                      <div className="overflow-hidden rounded-lg border border-[#30363D] bg-[#010409]">
                        {sceneImages[scene.number]?.status === 'success' && sceneImages[scene.number]?.imageUrl ? (
                          <img
                            src={sceneImages[scene.number].imageUrl}
                            alt={`Generated scene ${scene.number}`}
                            className="aspect-[9/16] w-full max-h-[520px] object-cover"
                          />
                        ) : (
                          <div className="flex aspect-[9/16] max-h-[520px] w-full items-center justify-center px-4 text-center text-xs leading-5 text-[#8B949E]">
                            {sceneImages[scene.number]?.status === 'generating'
                              ? `Generating scene ${scene.number} image...`
                              : sceneImages[scene.number]?.status === 'error'
                                ? 'Image not generated. Regenerate this scene or continue manually.'
                                : 'Generate scene images to preview this frame.'}
                          </div>
                        )}
                      </div>
                      {sceneImages[scene.number]?.status === 'success' && (
                        <p className="text-xs text-emerald-300">Generated by {sceneImages[scene.number].provider || imageProvider} as {sceneImages[scene.number].filename}</p>
                      )}
                      {sceneImages[scene.number]?.status === 'error' && (
                        <p className="text-xs leading-5 text-red-300">{sceneImages[scene.number].error || 'Provider failed or image was not generated.'}</p>
                      )}
                      <div>
                        <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#8B949E]">Image prompt</p>
                        <p className="leading-6 text-[#C9D1D9]">{scene.imagePrompt}</p>
                      </div>
                      <div>
                        <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#8B949E]">Image-to-video prompt</p>
                        <p className="leading-6 text-[#C9D1D9]">{scene.videoPrompt}</p>
                      </div>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div>
                          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#8B949E]">Caption text</p>
                          <p className="text-white">{scene.caption}</p>
                        </div>
                        <div>
                          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#8B949E]">Editing note</p>
                          <p className="text-[#C9D1D9]">{scene.editingNote}</p>
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <h2 className="text-lg font-bold text-white">Voiceover Script</h2>
                  <CopyButton text={packageData.voiceover}>Copy</CopyButton>
                </div>
                <p className="text-sm leading-6 text-[#C9D1D9]">{packageData.voiceover}</p>
              </div>

              <div className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <h2 className="text-lg font-bold text-white">Manual Workflow Checklist</h2>
                  <CopyButton text={workflowInstructions}>Copy</CopyButton>
                </div>
                <ol className="space-y-2 text-sm text-[#C9D1D9]">
                  {workflowInstructions.split('\n').slice(1).map((item, index) => (
                    <li key={item} className="flex gap-3">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#21262D] text-xs font-bold text-[#58A6FF]">{index + 1}</span>
                      <span>{item.replace(/^\d+\.\s*/, '')}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </section>

            <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-white">Colab Stitch Script</h2>
                  <p className="text-xs text-[#8B949E]">Resizes to 9:16, trims planned durations, overlays captions, and exports final_vertical_short.mp4.</p>
                </div>
                <CopyButton text={colabScript}>Copy Script</CopyButton>
              </div>
              <pre className="max-h-[420px] overflow-auto rounded-lg border border-[#30363D] bg-[#010409] p-4 text-xs leading-5 text-[#C9D1D9]">
                <code>{colabScript}</code>
              </pre>
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              {Object.entries(packageData.metadata).map(([platform, data]) => (
                <article key={platform} className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h2 className="text-lg font-bold capitalize text-white">{platform === 'youtube' ? 'YouTube Shorts' : platform === 'reels' ? 'Instagram Reels' : platform === 'facebook' ? 'Facebook Reels' : 'TikTok'}</h2>
                    <CopyButton text={Object.entries(data).map(([key, value]) => `${key}: ${value}`).join('\n')}>Copy</CopyButton>
                  </div>
                  {'title' in data && (
                    <div className="mb-3">
                      <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#8B949E]">Title</p>
                      <p className="text-sm text-white">{data.title}</p>
                    </div>
                  )}
                  <div className="mb-3">
                    <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#8B949E]">{'description' in data ? 'Description' : 'Caption'}</p>
                    <p className="whitespace-pre-wrap text-sm leading-6 text-[#C9D1D9]">{data.description || data.caption}</p>
                  </div>
                  <div>
                    <p className="mb-1 text-xs font-bold uppercase tracking-wide text-[#8B949E]">Hashtags</p>
                    <p className="text-sm text-[#58A6FF]">{data.hashtags}</p>
                  </div>
                </article>
              ))}
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}
