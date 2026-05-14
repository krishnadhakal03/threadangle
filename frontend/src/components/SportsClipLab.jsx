import React, { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../utils/api';

const DURATIONS = ['15s', '20s', '30s'];
const SPORTS = ['Football', 'EPL', 'Soccer', 'NBA', 'NFL', 'Other'];
const PLATFORMS = ['All', 'YouTube Shorts', 'TikTok', 'Reels'];
const TONES = ['cinematic', 'hype', 'emotional', 'rivalry', 'underdog', 'breaking-news'];
const PACING_MODES = [
  { value: 'balanced', label: 'Balanced cuts' },
  { value: 'hyper', label: 'Hyper fast cuts' },
  { value: 'story', label: 'Story tension' },
];
const MOTION_PRESETS = [
  { value: 'dramatic_push', label: 'Dramatic Push' },
  { value: 'crowd_shake', label: 'Crowd Shake' },
  { value: 'rivalry_faceoff_push', label: 'Rivalry Faceoff' },
  { value: 'penalty_pressure_zoom', label: 'Penalty Pressure' },
  { value: 'trophy_reveal', label: 'Trophy Reveal' },
  { value: 'stadium_flash', label: 'Stadium Flash' },
  { value: 'slow_zoom', label: 'Slow Zoom' },
  { value: 'pan_right', label: 'Pan Right' },
  { value: 'pan_left', label: 'Pan Left' },
  { value: 'hold', label: 'Hold' },
];
const FOOTBALL_TEMPLATE_OPTIONS = [
  { value: 'el-clasico', label: 'El Clasico Rivalry' },
  { value: 'epl-title-race', label: 'EPL Title Race' },
  { value: 'ucl-night', label: 'UCL Night' },
  { value: 'world-cup-knockout', label: 'World Cup Knockout Drama' },
  { value: 'penalty-shootout', label: 'Penalty Shootout Pressure' },
  { value: 'goat-debate', label: 'GOAT Debate' },
  { value: 'last-minute-comeback', label: 'Last-Minute Comeback' },
  { value: 'upset-alert', label: 'Upset Alert' },
  { value: 'star-player-watch', label: 'Star Player Watch' },
];
const IMAGE_PROVIDERS = [
  { value: 'huggingface', label: 'HuggingFace / fallback', mode: 'Free image adapter', risk: 'May fail when the local API has no model configured.' },
  { value: 'pollinations', label: 'Pollinations', mode: 'Free prompt image URL', risk: 'Remote image availability can vary by prompt.' },
];
const PERFORMANCE_STORAGE_KEY = 'threadangle_football_performance_logs_v1';
const SUPPORTED_EXTERNAL_CLIP_EXTENSIONS = ['.mp4', '.mov', '.webm'];
const GENERIC_VISUAL_GUIDANCE = [
  'Use generic sports editorial visuals inspired by the story context.',
  'Treat any named players as story labels only, not likeness targets.',
  'Do not recreate exact real-player likenesses, Messi-like faces, celebrity facial structure, tattoos, jersey names, kit logos, official badges, official crests, sponsor marks, or broadcast graphics.',
  'Prefer back view, silhouette, cropped hands, cropped boots, crowd reaction, stadium atmosphere, anonymous player angles, team-color energy, tactical details, and clean caption space.',
  'Use plain unbranded kits and invented visual motifs that cannot be mistaken for official club or national-team marks.',
].join(' ');

const FOOTBALL_TEMPLATES = {
  'el-clasico': {
    hookType: 'rivalry',
    topicCategory: 'rivalry',
    defaultTone: 'rivalry',
    hook: 'This rivalry still feels personal before kickoff.',
    body: 'Two giant clubs, one pressure cooker, and a result that can rewrite the week.',
    cta: 'Who owns this rivalry right now?',
    thumbnailText: ['RIVALRY NIGHT', 'WHO BLINKS FIRST?', 'CLASICO PRESSURE'],
    beats: [
      ['Cold open', 'The rivalry starts before the whistle.', 'two football captains staring each other down in a packed tunnel, scarf colors in the crowd, no official crests'],
      ['History flash', 'This fixture is never just another match.', 'split memory wall of past celebrations, tackles, and roaring supporters in generic red, white, and blue colors'],
      ['Star duel', 'One star moment can flip the story.', 'two elite footballers in opposing generic kits sprinting under stadium lights, ball between them'],
      ['Pressure spike', 'Every loose touch feels dangerous.', 'tight midfield duel, boots near the ball, crowd blurred into a wall of pressure'],
      ['Comment trigger', 'Tell me who has the bigger legacy.', 'dramatic split-screen poster with two fan sections facing each other'],
    ],
  },
  'epl-title-race': {
    hookType: 'stakes',
    topicCategory: 'title-race',
    defaultTone: 'hype',
    hook: 'The title race cannot survive a slip here.',
    body: 'Every point matters now, and this fixture has trap-game written all over it.',
    cta: 'Is this a title statement or a title collapse?',
    thumbnailText: ['TITLE RACE', 'NO ROOM TO SLIP', 'POINTS OR PANIC'],
    beats: [
      ['1-sec stakes', 'One mistake changes the table.', 'glowing league table graphic style background without real logos, anxious fans, floodlit pitch'],
      ['Contender focus', 'The favorite has to play like a champion.', 'football squad walking out under rain and floodlights, focused faces, generic kits'],
      ['Spoiler threat', 'The underdog only needs one clean chance.', 'counterattack forming with one forward breaking into open grass'],
      ['Final stretch', 'This is where champions separate.', 'clock near stoppage time, players shouting, crowd rising behind the goal'],
      ['Comment trigger', 'Would you trust them with the season on the line?', 'bold football debate poster with table pressure and empty space for captions'],
    ],
  },
  'ucl-night': {
    hookType: 'atmosphere',
    topicCategory: 'champions-night',
    defaultTone: 'cinematic',
    hook: 'European nights turn good teams into legends.',
    body: 'The lights, the anthem energy, and one mistake can change the entire tie.',
    cta: 'Who is built for this stage?',
    thumbnailText: ['EUROPEAN NIGHT', 'LEGEND OR EXIT?', 'UNDER THE LIGHTS'],
    beats: [
      ['Atmosphere', 'This is the night reputations are made.', 'massive European football stadium at night, blue-white lights, smoke, roaring stands'],
      ['First pressure', 'The first ten minutes will tell us everything.', 'players lining up before kickoff with intense faces and cinematic tunnel haze'],
      ['Tie breaker', 'One away goal feeling can shake the stadium.', 'striker winding up near the box, goalkeeper set, crowd frozen in anticipation'],
      ['Chaos beat', 'Nobody survives this level by playing safe.', 'scramble in the penalty area, bodies turning, ball loose near the spot'],
      ['Legacy close', 'This is how legends get remembered.', 'hero player silhouette facing the lights with fans behind them'],
    ],
  },
  'world-cup-knockout': {
    hookType: 'survival',
    topicCategory: 'world-cup',
    defaultTone: 'emotional',
    hook: 'Ninety minutes from survival or heartbreak.',
    body: 'World Cup knockout football turns every pass into pressure and every miss into a memory.',
    cta: 'Who survives this knockout night?',
    thumbnailText: ['SURVIVE OR GO HOME', 'WORLD CUP PRESSURE', 'KNOCKOUT NIGHT'],
    beats: [
      ['Survival hook', 'There is no tomorrow after this.', 'international football knockout match, packed stadium, flags without official emblems, players under pressure'],
      ['Nation stakes', 'A whole country is holding its breath.', 'supporters with face paint and flags, emotional close-ups, cinematic stadium glow'],
      ['Hero watch', 'This is where stars have to become leaders.', 'captain in generic national colors standing over the ball before a decisive play'],
      ['Turning point', 'One deflection can send you home.', 'ball flying through a crowded penalty area with goalkeeper diving'],
      ['Replay loop', 'Would you play brave or play safe?', 'final whistle tension, two benches reacting in opposite emotions'],
    ],
  },
  'penalty-shootout': {
    hookType: 'pressure',
    topicCategory: 'penalties',
    defaultTone: 'emotional',
    hook: 'A penalty shootout is football with nowhere to hide.',
    body: 'Five steps, one ball, one keeper, and a stadium loud enough to break legs.',
    cta: 'Who are you trusting from the spot?',
    thumbnailText: ['PENALTY PRESSURE', 'NO HIDING', 'FROM THE SPOT'],
    beats: [
      ['Spotlight', 'The walk from halfway feels endless.', 'footballer walking alone toward the penalty spot, crowd lights blurred, dramatic shadows'],
      ['Keeper mind game', 'The keeper only needs one read.', 'goalkeeper on the line, arms wide, intense eyes, net behind'],
      ['Contact beat', 'One strike can silence everything.', 'boot striking ball from the penalty spot, turf flying, high tension'],
      ['Reaction', 'This is where heroes and villains are made.', 'bench and fans reacting in emotional split frame'],
      ['Question close', 'Name your first penalty taker.', 'empty penalty spot under floodlights with bold negative space'],
    ],
  },
  'goat-debate': {
    hookType: 'debate',
    topicCategory: 'legacy',
    defaultTone: 'rivalry',
    hook: 'This debate never actually ends.',
    body: 'Goals, trophies, moments, longevity, aura: every side has receipts.',
    cta: 'Drop your GOAT and defend it.',
    thumbnailText: ['GOAT DEBATE', 'SETTLE THIS', 'LEGACY WAR'],
    beats: [
      ['Debate hook', 'Say the name and the comments explode.', 'football legacy debate poster with two anonymous superstar silhouettes and trophy light'],
      ['Receipts', 'Numbers tell one story.', 'stat-board inspired scene with football boots, trophies, and abstract numbers without real data claims'],
      ['Aura', 'Moments tell another.', 'packed stadium erupting after a bicycle-kick style silhouette, cinematic realism'],
      ['Counterpoint', 'But legacy depends on what you value.', 'split-screen of trophies, clutch goals, and captain leadership imagery'],
      ['Comment close', 'No fence-sitting: pick one.', 'bold social debate frame with comment space and football pitch texture'],
    ],
  },
  'last-minute-comeback': {
    hookType: 'comeback',
    topicCategory: 'comeback',
    defaultTone: 'hype',
    hook: 'The match is not dead until the last attack.',
    body: 'One chance, one cross, one bounce, and suddenly the impossible starts breathing.',
    cta: 'Have you seen a crazier comeback?',
    thumbnailText: ['LAST MINUTE', 'COMEBACK LOADING', 'NOT OVER'],
    beats: [
      ['Clock hook', 'Stoppage time changes everything.', 'stadium clock in stoppage time, players rushing forward, intense crowd'],
      ['Desperation', 'They are throwing everyone into the box.', 'goalkeeper and defenders in the opponent box for a final corner'],
      ['The chance', 'One touch can rewrite the result.', 'cross dropping into a crowded penalty area, dramatic motion blur'],
      ['Explosion', 'This is the moment the stadium loses it.', 'players sprinting to celebrate, crowd erupting, lights shaking'],
      ['Replay close', 'You have to watch the final attack again.', 'freeze-frame inspired comeback poster with time and score pressure'],
    ],
  },
  'upset-alert': {
    hookType: 'upset',
    topicCategory: 'underdog',
    defaultTone: 'underdog',
    hook: 'This has upset written all over it.',
    body: 'The favorite has the names, but the matchup pressure is quietly dangerous.',
    cta: 'Are you calling the upset before kickoff?',
    thumbnailText: ['UPSET ALERT', 'TRAP GAME', 'FAVORITE IN DANGER'],
    beats: [
      ['Warning hook', 'The favorite should be nervous.', 'underdog football team walking into hostile stadium, focused and fearless'],
      ['Mismatch twist', 'The trap is hiding in the details.', 'tactical board style image showing pressing lanes and open space, no real logos'],
      ['Danger player', 'One runner can ruin the script.', 'fast winger sprinting into space behind a defensive line'],
      ['Pressure swing', 'The crowd can feel the momentum changing.', 'favorite team under pressure near their own box, fans rising'],
      ['Prediction close', 'Would you bet the upset?', 'dramatic upset poster with giant-versus-underdog framing'],
    ],
  },
  'star-player-watch': {
    hookType: 'player-watch',
    topicCategory: 'spotlight',
    defaultTone: 'cinematic',
    hook: 'All eyes are on one player tonight.',
    body: 'The matchup is bigger than one name, but the story follows every touch they take.',
    cta: 'Is this a statement game?',
    thumbnailText: ['STAR WATCH', 'STATEMENT GAME', 'ALL EYES ON HIM'],
    beats: [
      ['Spotlight hook', 'Every touch is going to be judged.', 'star footballer silhouette tying boots under locker-room light, generic kit'],
      ['Role', 'The team needs more than highlights.', 'player scanning the pitch before receiving the ball, teammates moving around them'],
      ['Pressure test', 'The defense knows the whole plan.', 'two defenders closing down a dribbler near the touchline'],
      ['Signature moment', 'One signature play can own the timeline.', 'footballer striking or assisting in cinematic action with stadium lights'],
      ['Comment close', 'What counts as a good game for him?', 'player spotlight poster with room for stat overlays and captions'],
    ],
  },
};

const EXAMPLES = {
  nba: {
    label: 'NBA hot game today',
    eventTopic: 'Spurs vs Timberwolves Game 5, May 12, 2026',
    sport: 'NBA',
    teamsPlayers: 'San Antonio Spurs, Minnesota Timberwolves, Victor Wembanyama, Anthony Edwards',
    targetPlatform: 'All',
    duration: '20s',
    pacingMode: 'balanced',
    tone: 'hype',
    hook: 'Wemby is back under playoff pressure tonight.',
    body: 'Game 5 is tied 2-2, the stage is in San Antonio, and one run could swing the whole series.',
    cta: 'Who owns Game 5: Wemby or Ant?',
    template: 'star-player-watch',
    worldCupMode: false,
  },
  city: {
    label: 'Manchester City game tomorrow',
    eventTopic: 'Manchester City vs Crystal Palace, May 13, 2026',
    sport: 'EPL',
    teamsPlayers: 'Manchester City, Crystal Palace, Erling Haaland, Phil Foden, Eberechi Eze',
    targetPlatform: 'All',
    duration: '20s',
    pacingMode: 'balanced',
    tone: 'cinematic',
    hook: 'City cannot blink in the title race tomorrow.',
    body: 'Crystal Palace arrive at the Etihad with spoiler energy while City chase every point under pressure.',
    cta: 'Will City handle the pressure or slip?',
    template: 'epl-title-race',
    worldCupMode: false,
  },
  knockout: {
    label: 'World Cup knockout preset',
    eventTopic: 'Argentina vs France knockout rematch',
    sport: 'Football',
    teamsPlayers: 'Argentina, France, Lionel Messi, Kylian Mbappe',
    targetPlatform: 'All',
    duration: '20s',
    pacingMode: 'hyper',
    tone: 'emotional',
    hook: 'Ninety minutes from survival or heartbreak.',
    body: 'World Cup knockout football turns every touch into pressure and every miss into history.',
    cta: 'Who survives this knockout night?',
    template: 'world-cup-knockout',
    worldCupMode: true,
  },
};

const INITIAL_FORM = EXAMPLES.nba;

function getTemplate(form) {
  return FOOTBALL_TEMPLATES[form.template] || FOOTBALL_TEMPLATES['star-player-watch'];
}

function applyTemplateToForm(form, templateKey, keepTopic = true) {
  const template = FOOTBALL_TEMPLATES[templateKey] || FOOTBALL_TEMPLATES['star-player-watch'];
  return {
    ...form,
    sport: form.sport === 'NBA' || form.sport === 'NFL' ? 'Football' : form.sport,
    template: templateKey,
    tone: template.defaultTone || form.tone,
    hook: keepTopic && form.hook ? form.hook : template.hook,
    body: keepTopic && form.body ? form.body : template.body,
    cta: keepTopic && form.cta ? form.cta : template.cta,
    worldCupMode: templateKey === 'world-cup-knockout' ? true : Boolean(form.worldCupMode),
  };
}

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

function getFastCutDurations(totalDuration, count, pacingMode = 'balanced') {
  const total = Number.parseInt(totalDuration, 10) || 20;
  const weightsByMode = {
    hyper: [1, 1.25, 1, 1.15, 0.95, 0.9, 0.85, 0.8],
    balanced: [1, 1.2, 1.1, 1.05, 0.95, 0.9, 0.85, 0.8],
    story: [1, 1.35, 1.25, 1.1, 1, 0.95, 0.9, 0.85],
  };
  const weights = weightsByMode[pacingMode] || weightsByMode.balanced;
  const activeWeights = Array.from({ length: count }, (_, index) => weights[index] || 1);
  const weightTotal = activeWeights.reduce((sum, weight) => sum + weight, 0);
  let secondsLeft = total;

  return activeWeights.map((weight, index) => {
    const remaining = count - index;
    if (remaining === 1) return Math.max(1, secondsLeft);
    const minForRest = remaining - 1;
    const raw = Math.round((total * weight) / weightTotal);
    const capped = Math.min(Math.max(1, raw), secondsLeft - minForRest);
    secondsLeft -= capped;
    return capped;
  });
}

function countWords(text) {
  return String(text || '').trim().split(/\s+/).filter(Boolean).length;
}

function captionDensityScore(caption, duration) {
  const wordsPerSecond = countWords(caption) / Math.max(1, duration);
  if (wordsPerSecond <= 2.4) return 92;
  if (wordsPerSecond <= 3.1) return 78;
  if (wordsPerSecond <= 3.8) return 62;
  return 46;
}

function buildRetentionPlan(scene, index, totalScenes, pacingMode) {
  const hookScene = index === 0;
  const endingScene = index === totalScenes - 1;
  const energyCurve = pacingMode === 'story'
    ? [96, 76, 84, 91, 88, 94, 90, 86]
    : pacingMode === 'hyper'
      ? [98, 88, 94, 90, 96, 86, 92, 89]
      : [96, 82, 88, 85, 92, 86, 90, 84];
  const emotionalArc = hookScene
    ? 'Instant pressure spike'
    : endingScene
      ? 'Open-loop comment payoff'
      : index < totalScenes / 2
        ? 'Stakes escalation'
        : 'Decision tension';

  return {
    energyScore: energyCurve[index] || 84,
    captionDensityScore: captionDensityScore(scene.caption, scene.duration),
    emotionalArc,
    recommendedCut: hookScene ? '0.8s visual hook before the first full caption' : `${scene.duration}s beat-matched cut`,
    transition: hookScene ? 'smash cut from black' : endingScene ? 'snap zoom into loop frame' : 'match cut on movement',
    beatDrop: hookScene ? '0.4s' : `${Math.max(1, Math.round(scene.duration * 0.55))}s`,
    captionPlacement: hookScene ? 'upper-middle, 3-5 words max' : 'lower third with safe margins',
    curiosityGap: hookScene ? 'Hide the answer until scene 4.' : endingScene ? 'Ask for a side, not a generic opinion.' : 'Delay the reveal by one more cut.',
    patternInterrupt: hookScene ? 'Start on a face, not a wide stadium.' : index % 2 === 0 ? 'Speed-ramp into freeze frame.' : 'Cut to crowd reaction before action resolves.',
    replayLoop: endingScene ? `End on "${scene.caption}" then hard cut back to the opening pressure frame.` : 'Keep this beat short enough that the viewer expects the next cut.',
  };
}

function makeHashtags(form) {
  const topicTags = form.teamsPlayers
    .split(',')
    .map((item) => item.trim().replace(/[^a-zA-Z0-9]/g, ''))
    .filter(Boolean)
    .slice(0, 4)
    .map((item) => `#${item}`);

  const sportTag = `#${form.sport.replace(/[^a-zA-Z0-9]/g, '') || 'Sports'}`;
  const template = getTemplate(form);
  const footballTags = ['#Football', '#Soccer', '#Shorts'];
  const worldCupTags = form.worldCupMode ? ['#WorldCup', '#WorldCup2026'] : [];
  const categoryTag = template.topicCategory ? [`#${template.topicCategory.replace(/[^a-zA-Z0-9]/g, '')}`] : [];
  return [...new Set([...footballTags, sportTag, ...worldCupTags, '#GameDay', ...categoryTag, ...topicTags])].slice(0, 10);
}

function buildScenes(form) {
  const total = Number.parseInt(form.duration, 10) || 20;
  const template = getTemplate(form);
  const count = total <= 15 ? 4 : total >= 30 ? Math.min(8, template.beats.length + 1) : Math.min(6, template.beats.length);
  const durations = getFastCutDurations(form.duration, count, form.pacingMode);
  const bodyLines = splitText(form.body);
  const storyContext = form.teamsPlayers || form.eventTopic || 'the matchup';
  const footballContext = form.worldCupMode ? 'World Cup mode, national-team stakes, knockout pressure.' : 'Football-first short-form package.';

  const beats = template.beats.map(([label, fallbackCaption, visual], index) => ({
    label,
    caption: index === 0 ? (form.hook || fallbackCaption) : index === template.beats.length - 1 ? (form.cta || fallbackCaption) : (bodyLines[index - 1] || fallbackCaption),
    visual,
    motion: index === 0
      ? 'hard cut in under one second, fast push, crowd flash, immediate caption pop'
      : index === template.beats.length - 1
        ? 'snap zoom into final frame, half-second hold for comments, clean loop back to opening image'
        : 'fast handheld push, speed ramp, match cut on beat, keep motion readable in 9:16',
    note: index === 0
      ? 'Hook must land in the first second. Use the shortest caption on the strongest frame.'
      : index === template.beats.length - 1
        ? 'End as a comment prompt and make the final frame loop naturally into scene 1.'
        : 'Keep the cut tight and caption short enough to read on mobile.',
  }));

  if (count > beats.length) {
    beats.push({
      label: 'Final punch',
      caption: form.cta || template.cta,
      visual: 'vertical football debate poster with stadium lights, supporter emotion, and clean caption space',
      motion: 'quick zoom out to final frame, subtle crowd pulse, hard cut back to the opener',
      note: 'Use only when the 30 second version needs a stronger final CTA.',
    });
  }

  return beats.slice(0, count).map((beat, index) => {
    const scene = {
      number: index + 1,
      label: beat.label,
      duration: durations[index],
      imagePrompt: [
        `Vertical 9:16 football short scene for "${form.eventTopic}".`,
        footballContext,
        `Tone: ${form.tone}. Story context: ${storyContext}.`,
        GENERIC_VISUAL_GUIDANCE,
        `${beat.visual}.`,
        'Cinematic sports editorial style, realistic lighting, sharp anonymous subjects, readable negative space for captions.',
      ].join(' '),
      videoPrompt: [
        `Animate this image as a ${durations[index]} second vertical sports clip.`,
        `${beat.motion}.`,
        'Keep faces and uniforms stable, avoid text artifacts, preserve 9:16 framing, leave lower third clear for captions.',
      ].join(' '),
      caption: beat.caption,
      editingNote: beat.note,
      thumbnailText: template.thumbnailText[index % template.thumbnailText.length],
    };

    return {
      ...scene,
      retention: buildRetentionPlan(scene, index, count, form.pacingMode),
    };
  });
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
  const template = getTemplate(form);
  const shortTitle = `${titleCore}: ${template.topicCategory.replace(/-/g, ' ')}`;
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
    template: {
      name: FOOTBALL_TEMPLATE_OPTIONS.find((option) => option.value === form.template)?.label || 'Football Template',
      hookType: template.hookType,
      topicCategory: template.topicCategory,
      thumbnailText: template.thumbnailText.join(' | '),
      worldCupMode: form.worldCupMode ? 'Enabled' : 'Off',
    },
  };
}

function buildPromptText(packageData) {
  return packageData.scenes.map((scene) => [
    `Scene ${scene.number}: ${scene.label}`,
    `Duration: ${scene.duration}s`,
    `Energy score: ${scene.retention.energyScore}/100`,
    `Caption density score: ${scene.retention.captionDensityScore}/100`,
    `Emotional arc: ${scene.retention.emotionalArc}`,
    `Recommended cut: ${scene.retention.recommendedCut}`,
    `Transition: ${scene.retention.transition}`,
    `Beat drop timing: ${scene.retention.beatDrop}`,
    `Caption placement: ${scene.retention.captionPlacement}`,
    `Curiosity gap: ${scene.retention.curiosityGap}`,
    `Pattern interrupt: ${scene.retention.patternInterrupt}`,
    `Replay loop: ${scene.retention.replayLoop}`,
    `Image prompt: ${scene.imagePrompt}`,
    `Image-to-video prompt: ${scene.videoPrompt}`,
    `Caption: ${scene.caption}`,
    `Editing note: ${scene.editingNote}`,
  ].join('\n')).join('\n\n');
}

function buildMetadataText(metadata) {
  return [
    `Template\nName: ${metadata.template.name}\nHook type: ${metadata.template.hookType}\nTopic category: ${metadata.template.topicCategory}\nThumbnail text options: ${metadata.template.thumbnailText}\nWorld Cup mode: ${metadata.template.worldCupMode}`,
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

async function imageUrlToBytes(imageUrl) {
  if (String(imageUrl || '').startsWith('data:')) {
    return dataUrlToBytes(imageUrl);
  }

  const response = await fetch(imageUrl);
  if (!response.ok) {
    throw new Error(`Unable to download image asset (${response.status})`);
  }

  return new Uint8Array(await response.arrayBuffer());
}

function getImageProviderProfile(providerValue) {
  return IMAGE_PROVIDERS.find((provider) => provider.value === providerValue) || IMAGE_PROVIDERS[0];
}

function loadPerformanceLogs() {
  try {
    const raw = window.localStorage.getItem(PERFORMANCE_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function scorePerformance(log) {
  const views = Number(log.views) || 0;
  const likes = Number(log.likes) || 0;
  const comments = Number(log.comments) || 0;
  const shares = Number(log.shares) || 0;
  const subscribers = Number(log.subscribers) || 0;
  return views + likes * 5 + comments * 25 + shares * 35 + subscribers * 120;
}

function classifyPerformance(log) {
  const views = Number(log.views) || 0;
  const comments = Number(log.comments) || 0;
  const subscribers = Number(log.subscribers) || 0;
  if (views >= 2000 || comments >= 12 || subscribers >= 3) return 'winner';
  if (views < 250 && comments === 0 && subscribers === 0) return 'loser';
  return 'watch';
}

function splitTrackedTerms(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function summarizePerformance(logs) {
  const buckets = {
    template: new Map(),
    topic: new Map(),
    platform: new Map(),
    team: new Map(),
  };

  logs.forEach((log) => {
    const score = scorePerformance(log);
    const add = (bucket, key) => {
      if (!key) return;
      const current = bucket.get(key) || { key, posts: 0, score: 0, views: 0, comments: 0, subscribers: 0, winners: 0, losers: 0 };
      current.posts += 1;
      current.score += score;
      current.views += Number(log.views) || 0;
      current.comments += Number(log.comments) || 0;
      current.subscribers += Number(log.subscribers) || 0;
      current.winners += log.resultTag === 'winner' ? 1 : 0;
      current.losers += log.resultTag === 'loser' ? 1 : 0;
      bucket.set(key, current);
    };

    add(buckets.template, log.template);
    add(buckets.topic, log.topicCategory);
    add(buckets.platform, log.platform);
    splitTrackedTerms(log.teamsPlayers).forEach((term) => add(buckets.team, term));
  });

  const rank = (bucket) => Array.from(bucket.values())
    .sort((a, b) => (b.score / b.posts) - (a.score / a.posts))
    .slice(0, 4);

  return {
    templates: rank(buckets.template),
    topics: rank(buckets.topic),
    platforms: rank(buckets.platform),
    teams: rank(buckets.team),
  };
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

function revokeObjectUrl(value) {
  if (typeof value === 'string' && value.startsWith('blob:')) {
    URL.revokeObjectURL(value);
  }
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

function motionPresetLabel(value) {
  return MOTION_PRESETS.find((preset) => preset.value === value)?.label || String(value || 'Motion').replace(/_/g, ' ');
}

function inferMotionPreset(scene) {
  const haystack = [
    scene?.label,
    scene?.caption,
    scene?.imagePrompt,
    scene?.thumbnailText,
  ].join(' ').toLowerCase();

  if (/(rivalry|faceoff|face-off|duel|staring|split-screen|legacy)/.test(haystack)) return 'rivalry_faceoff_push';
  if (/(penalty|spot|keeper|shootout)/.test(haystack)) return 'penalty_pressure_zoom';
  if (/(trophy|final|winner|champion|legacy close|payoff)/.test(haystack)) return 'trophy_reveal';
  if (/(crowd|supporter|fans|erupts|stadium loses|celebration)/.test(haystack)) return 'crowd_shake';
  if (/(stadium|lights|flash|anthem|night)/.test(haystack)) return 'stadium_flash';
  return scene?.number === 1 ? 'dramatic_push' : 'slow_zoom';
}

export default function SportsClipLab() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [generatedForm, setGeneratedForm] = useState(INITIAL_FORM);
  const [imageProvider, setImageProvider] = useState('huggingface');
  const [sceneImages, setSceneImages] = useState({});
  const [sceneMotionPreviews, setSceneMotionPreviews] = useState({});
  const [sceneMotionStyles, setSceneMotionStyles] = useState({});
  const [sceneClipDecisions, setSceneClipDecisions] = useState({});
  const [generatingAll, setGeneratingAll] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);
  const [activeScene, setActiveScene] = useState(null);
  const [imageBatchMessage, setImageBatchMessage] = useState(null);
  const [finalStitch, setFinalStitch] = useState({ status: 'idle', error: null });
  const externalClipInputRefs = useRef({});
  const objectUrlsRef = useRef(new Set());
  const [performanceLogs, setPerformanceLogs] = useState(() => loadPerformanceLogs());
  const [performanceForm, setPerformanceForm] = useState({
    platform: 'YouTube Shorts',
    views: '',
    likes: '',
    comments: '',
    shares: '',
    subscribers: '',
    postingTime: '',
    retentionNotes: '',
    replayabilityNotes: '',
  });

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
  const approvedSceneCount = packageData.scenes.filter((scene) => sceneClipDecisions[scene.number]?.approved).length;
  const allScenesApproved = approvedSceneCount === packageData.scenes.length;
  const activeImageProvider = getImageProviderProfile(imageProvider);
  const performanceSummary = useMemo(() => summarizePerformance(performanceLogs), [performanceLogs]);

  useEffect(() => () => {
    objectUrlsRef.current.forEach((url) => revokeObjectUrl(url));
    objectUrlsRef.current.clear();
  }, []);

  const trackObjectUrl = (url) => {
    if (typeof url === 'string' && url.startsWith('blob:')) {
      objectUrlsRef.current.add(url);
    }
    return url;
  };

  const releaseObjectUrl = (url) => {
    if (typeof url === 'string' && url.startsWith('blob:')) {
      revokeObjectUrl(url);
      objectUrlsRef.current.delete(url);
    }
  };

  const releaseAllObjectUrls = () => {
    objectUrlsRef.current.forEach((url) => revokeObjectUrl(url));
    objectUrlsRef.current.clear();
  };

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const updateTemplate = (templateKey) => {
    setForm((current) => applyTemplateToForm(current, templateKey, false));
  };

  const updatePerformanceField = (key, value) => {
    setPerformanceForm((current) => ({ ...current, [key]: value }));
  };

  const savePerformanceLog = () => {
    const nextLog = {
      id: `${Date.now()}`,
      createdAt: new Date().toISOString(),
      eventTopic: packageData.form.eventTopic,
      platform: performanceForm.platform,
      postingTime: performanceForm.postingTime,
      template: packageData.metadata.template.name,
      hookType: packageData.metadata.template.hookType,
      topicCategory: packageData.metadata.template.topicCategory,
      teamsPlayers: packageData.form.teamsPlayers,
      hook: packageData.form.hook,
      views: Number(performanceForm.views) || 0,
      likes: Number(performanceForm.likes) || 0,
      comments: Number(performanceForm.comments) || 0,
      shares: Number(performanceForm.shares) || 0,
      subscribers: Number(performanceForm.subscribers) || 0,
      retentionNotes: performanceForm.retentionNotes,
      replayabilityNotes: performanceForm.replayabilityNotes,
    };
    nextLog.resultTag = classifyPerformance(nextLog);
    nextLog.score = scorePerformance(nextLog);

    const nextLogs = [nextLog, ...performanceLogs].slice(0, 80);
    setPerformanceLogs(nextLogs);
    window.localStorage.setItem(PERFORMANCE_STORAGE_KEY, JSON.stringify(nextLogs));
    setPerformanceForm((current) => ({
      ...current,
      views: '',
      likes: '',
      comments: '',
      shares: '',
      subscribers: '',
      retentionNotes: '',
      replayabilityNotes: '',
    }));
  };

  const generatePackage = () => {
    releaseAllObjectUrls();
    setGeneratedForm({ ...form });
    setSceneImages({});
    setSceneMotionPreviews({});
    setSceneMotionStyles({});
    setSceneClipDecisions({});
    setFinalStitch({ status: 'idle', error: null });
    setImageBatchMessage(null);
  };

  const generateSceneImage = async (scene, forceVariation = false) => {
    const sceneKey = scene.number;
    setActiveScene(sceneKey);
    releaseObjectUrl(sceneMotionPreviews[sceneKey]?.videoUrl);
    if (sceneClipDecisions[sceneKey]?.source === 'external_upload') {
      releaseObjectUrl(sceneClipDecisions[sceneKey]?.videoUrl);
    }
    setSceneMotionPreviews((current) => {
      const next = { ...current };
      delete next[sceneKey];
      return next;
    });
    setSceneMotionStyles((current) => {
      const next = { ...current };
      delete next[sceneKey];
      return next;
    });
    setSceneClipDecisions((current) => {
      return {
        ...current,
        [sceneKey]: {
          status: 'needs_decision',
          source: null,
          approved: false,
          message: 'Image changed. Review motion or upload a clip again before approval.',
        },
      };
    });
    releaseObjectUrl(finalStitch.videoUrl);
    setFinalStitch({ status: 'idle', error: null });
    setSceneImages((current) => ({
      ...current,
      [sceneKey]: {
        ...current[sceneKey],
        status: 'generating',
        error: null,
      },
    }));

    try {
      const providerProfile = getImageProviderProfile(imageProvider);
      const data = await api.regenerateSceneImage({
        scene_index: scene.number - 1,
        scene_description: scene.imagePrompt,
        character_profile: {
          type: `${packageData.form.sport} sports scene`,
          style: 'cinematic sports editorial',
          event: packageData.form.eventTopic,
          story_context: packageData.form.teamsPlayers,
          likeness_policy: 'generic anonymous athletes only; named players are context labels, not face targets; no Messi-like faces, exact real-player likeness, jersey names, logos, tattoos, official badges, crests, sponsor marks, or broadcast graphics; prefer back views, silhouettes, cropped hands/boots, crowd, stadium, and anonymous player angles',
          provider_mode: providerProfile.mode,
          manual_approval_required: true,
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
          providerMode: providerProfile.mode,
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

  const generateMotionPreview = async (scene) => {
    const sceneKey = scene.number;
    const image = sceneImages[sceneKey];
    if (image?.status !== 'success' || !image.imageUrl) {
      setSceneMotionPreviews((current) => ({
        ...current,
        [sceneKey]: {
          status: 'error',
          error: 'Generate an image for this scene before creating a local motion preview.',
        },
      }));
      return;
    }

    const motionStyle = sceneMotionStyles[sceneKey] || inferMotionPreset(scene);
    setSceneMotionPreviews((current) => ({
      ...current,
      [sceneKey]: {
        ...current[sceneKey],
        status: 'generating',
        error: null,
      },
    }));
    if (sceneClipDecisions[sceneKey]?.source === 'local_motion') {
      releaseObjectUrl(finalStitch.videoUrl);
      setFinalStitch({ status: 'idle', error: null });
    }
    setSceneClipDecisions((current) => {
      if (current[sceneKey]?.source !== 'local_motion') return current;
      return {
        ...current,
        [sceneKey]: {
          status: 'needs_decision',
          source: null,
          approved: false,
          message: 'Motion preview is being regenerated. Approve the new clip before final stitch.',
        },
      };
    });

    try {
      const data = await api.generateSportsMotionPreview({
        scene_index: scene.number - 1,
        image_url: image.imageUrl,
        duration: Math.max(1, Math.min(6, Number(scene.duration) || 3)),
        motion_style: motionStyle,
        caption: scene.caption,
      });
      const { blobUrl } = await api.fetchVideoBlob(data.preview_url || data.download_url);
      const trackedBlobUrl = trackObjectUrl(blobUrl);
      releaseObjectUrl(sceneMotionPreviews[sceneKey]?.videoUrl);
      setSceneMotionPreviews((current) => {
        return {
          ...current,
          [sceneKey]: {
            status: 'success',
            videoUrl: trackedBlobUrl,
            downloadUrl: data.download_url,
            videoFile: data.video_file,
            generationId: data.generation_id,
            provider: data.provider,
            duration: data.duration,
            motionStyle: data.motion_style,
            approvalRequired: Boolean(data.approval_required),
            error: null,
          },
        };
      });
    } catch (err) {
      setSceneMotionPreviews((current) => ({
        ...current,
        [sceneKey]: {
          status: 'error',
          error: err?.message || 'Local motion preview failed.',
        },
      }));
    }
  };

  const updateMotionStyle = (scene, motionStyle) => {
    const sceneKey = scene.number;
    setSceneMotionStyles((current) => ({
      ...current,
      [sceneKey]: motionStyle,
    }));

    if (sceneClipDecisions[sceneKey]?.source === 'local_motion') {
      setSceneClipDecisions((current) => ({
        ...current,
        [sceneKey]: {
          status: 'needs_decision',
          source: null,
          approved: false,
          message: 'Motion preset changed. Regenerate and approve the new local preview before final stitch.',
        },
      }));
      releaseObjectUrl(finalStitch.videoUrl);
      setFinalStitch({ status: 'idle', error: null });
    }
  };

  const approveLocalMotionClip = (scene) => {
    const sceneKey = scene.number;
    const preview = sceneMotionPreviews[sceneKey];
    if (preview?.status !== 'success' || !preview.videoUrl) {
      setSceneClipDecisions((current) => ({
        ...current,
        [sceneKey]: {
          status: 'blocked',
          source: 'local_motion',
          approved: false,
          message: 'Render a local motion preview before approving it.',
        },
      }));
      return;
    }
    if (!preview.videoFile) {
      setSceneClipDecisions((current) => ({
        ...current,
        [sceneKey]: {
          status: 'blocked',
          source: 'local_motion',
          approved: false,
          message: 'Local motion preview is missing its backend video file. Render the preview again before approving.',
        },
      }));
      return;
    }

    if (sceneClipDecisions[sceneKey]?.source === 'external_upload') {
      releaseObjectUrl(sceneClipDecisions[sceneKey]?.videoUrl);
    }
    setSceneClipDecisions((current) => ({
      ...current,
      [sceneKey]: {
        status: 'approved',
        source: 'local_motion',
        approved: true,
        videoUrl: preview.videoUrl,
        downloadUrl: preview.downloadUrl,
        videoFile: preview.videoFile,
        generationId: preview.generationId,
        duration: preview.duration,
        motionStyle: preview.motionStyle,
        fileName: `scene${scene.number}_local_motion.mp4`,
        message: 'Approved local motion preview for final stitch.',
      },
    }));
  };

  const uploadExternalClip = (scene, file) => {
    if (!file) return;
    const sceneKey = scene.number;
    const extension = `.${String(file.name || '').split('.').pop()}`.toLowerCase();
    if (!SUPPORTED_EXTERNAL_CLIP_EXTENSIONS.includes(extension)) {
      if (sceneClipDecisions[sceneKey]?.source === 'external_upload') {
        releaseObjectUrl(sceneClipDecisions[sceneKey]?.videoUrl);
      }
      setSceneClipDecisions((current) => ({
        ...current,
        [sceneKey]: {
          status: 'blocked',
          source: 'external_upload',
          approved: false,
          message: 'Unsupported uploaded clip format. Use MP4, MOV, or WebM.',
        },
      }));
      return;
    }

    const videoUrl = trackObjectUrl(URL.createObjectURL(file));
    if (sceneClipDecisions[sceneKey]?.source === 'external_upload') {
      releaseObjectUrl(sceneClipDecisions[sceneKey]?.videoUrl);
    }
    setSceneClipDecisions((current) => ({
      ...current,
      [sceneKey]: {
        status: 'needs_review',
        source: 'external_upload',
        approved: false,
        videoUrl,
        file,
        fileName: file.name,
        duration: scene.duration,
        message: 'External clip uploaded for this browser session. Review and approve it before final stitch.',
      },
    }));
  };

  const approveExternalClip = (scene) => {
    const sceneKey = scene.number;
    const decision = sceneClipDecisions[sceneKey];
    if (decision?.source !== 'external_upload' || !decision.videoUrl) return;

    setSceneClipDecisions((current) => ({
      ...current,
      [sceneKey]: {
        ...current[sceneKey],
        status: 'approved',
        approved: true,
        message: 'Approved uploaded external clip for final stitch.',
      },
    }));
  };

  const createFinalStitch = async () => {
    const missingScenes = packageData.scenes.filter((scene) => !sceneClipDecisions[scene.number]?.approved);
    if (missingScenes.length) {
      setFinalStitch({
        status: 'error',
        error: `Approve every scene before final stitch. Missing: ${missingScenes.map((scene) => `Scene ${scene.number}`).join(', ')}.`,
      });
      return;
    }

    const missingLocalFiles = packageData.scenes.filter((scene) => {
      const decision = sceneClipDecisions[scene.number];
      return decision?.source === 'local_motion' && !decision.videoFile;
    });
    if (missingLocalFiles.length) {
      setFinalStitch({
        status: 'error',
        error: `Approved local preview is missing its backend video file for ${missingLocalFiles.map((scene) => `Scene ${scene.number}`).join(', ')}. Regenerate and approve that local preview.`,
      });
      return;
    }

    const approvedScenes = packageData.scenes.map((scene) => {
      const decision = sceneClipDecisions[scene.number];
      return {
        scene_number: scene.number,
        label: scene.label,
        caption: scene.caption,
        duration: Number(decision.duration || scene.duration || 3),
        source: decision.source,
        approved: true,
        video_file: decision.videoFile || null,
        file_name: decision.fileName || null,
        motion_style: decision.motionStyle || null,
      };
    });

    const formData = new FormData();
    formData.append('scenes_json', JSON.stringify(approvedScenes));
    formData.append('metadata_json', JSON.stringify(packageData.metadata));
    formData.append('voiceover_text', packageData.voiceover);

    const externalSceneNumbers = [];
    packageData.scenes.forEach((scene) => {
      const decision = sceneClipDecisions[scene.number];
      if (decision?.source === 'external_upload' && decision.file) {
        externalSceneNumbers.push(scene.number);
        formData.append('external_files', decision.file, decision.fileName || `scene${scene.number}.mp4`);
      }
    });
    formData.append('external_scene_numbers_json', JSON.stringify(externalSceneNumbers));

    releaseObjectUrl(finalStitch.videoUrl);
    setFinalStitch({ status: 'rendering', error: null });
    try {
      const data = await api.createSportsFinalStitch(formData);
      let trackedBlobUrl = null;
      let previewFetchError = null;
      try {
        const { blobUrl } = await api.fetchVideoBlob(data.preview_url || data.download_url);
        trackedBlobUrl = trackObjectUrl(blobUrl);
      } catch (previewErr) {
        previewFetchError = previewErr?.message || 'Browser preview fetch failed. Use the direct download link or check the local HTTPS certificate.';
      }
      setFinalStitch({
        status: 'success',
        error: null,
        videoUrl: trackedBlobUrl,
        previewFetchError,
        downloadUrl: data.download_url,
        directDownloadUrl: api.getVideoAssetUrl(data.download_url),
        generationId: data.generation_id,
        runId: data.run_id,
        videoFile: data.video_file,
        metadataFile: data.metadata_file,
        sceneCount: data.scene_count,
        costs: data.costs,
      });
    } catch (err) {
      setFinalStitch({
        status: 'error',
        error: err?.message || 'Final stitch failed.',
      });
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

  const downloadSceneImagesZip = async () => {
    const readyImages = packageData.scenes
      .map((scene) => ({ scene, image: sceneImages[scene.number] }))
      .filter(({ image }) => image?.status === 'success' && image.imageUrl);

    if (!readyImages.length) {
      setImageBatchMessage({ type: 'error', text: 'No generated images are ready to download.' });
      return;
    }

    setDownloadingZip(true);
    try {
      const imageFiles = [];
      for (const { image } of readyImages) {
        imageFiles.push({
          name: image.filename,
          bytes: await imageUrlToBytes(image.imageUrl),
        });
      }

      const manifest = readyImages.map(({ scene, image }) => [
        `Scene ${scene.number}: ${scene.label}`,
        `Filename: ${image.filename}`,
        `Provider: ${image.provider || imageProvider}`,
        `Caption: ${scene.caption}`,
        `Image prompt: ${image.promptUsed || scene.imagePrompt}`,
        `Image-to-video prompt: ${scene.videoPrompt}`,
      ].join('\n')).join('\n\n');

      downloadBlob(createZip([
        ...imageFiles,
        { name: 'scene-prompts.txt', bytes: new Uint8Array(new TextEncoder().encode(manifest)) },
      ]), 'threadangle-football-scene-images.zip');
      setImageBatchMessage({ type: 'success', text: `Downloaded ${imageFiles.length} images with prompt manifest.` });
    } catch (err) {
      setImageBatchMessage({ type: 'error', text: err?.message || 'Could not package generated images. Copy prompts and download images manually.' });
    } finally {
      setDownloadingZip(false);
    }
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
                  releaseAllObjectUrls();
                  setForm(example);
                  setGeneratedForm(example);
                  setSceneImages({});
                  setSceneMotionPreviews({});
                  setSceneMotionStyles({});
                  setSceneClipDecisions({});
                  setFinalStitch({ status: 'idle', error: null });
                  setImageBatchMessage(null);
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
              <Field label="Football template">
                <Select value={form.template || 'star-player-watch'} onChange={(e) => updateTemplate(e.target.value)}>
                  {FOOTBALL_TEMPLATE_OPTIONS.map((template) => <option key={template.value} value={template.value}>{template.label}</option>)}
                </Select>
              </Field>
              <label className="flex items-center gap-3 rounded-lg border border-[#30363D] bg-[#0D1117] px-3 py-2.5 text-sm text-[#C9D1D9]">
                <input
                  type="checkbox"
                  checked={Boolean(form.worldCupMode)}
                  onChange={(e) => updateField('worldCupMode', e.target.checked)}
                  className="h-4 w-4 accent-[#1F6FEB]"
                />
                <span>World Cup mode</span>
              </label>
              <Field label="Teams/players story context">
                <TextArea rows={3} value={form.teamsPlayers} onChange={(e) => updateField('teamsPlayers', e.target.value)} placeholder="Teams, players, rivalry angle" />
                <p className="mt-1.5 text-[11px] leading-4 text-[#8B949E]">
                  Used for story context only. Generated images should use generic athletes, team-color energy, and matchup emotion instead of exact player likeness.
                </p>
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
              <Field label="Pacing planner">
                <Select value={form.pacingMode || 'balanced'} onChange={(e) => updateField('pacingMode', e.target.value)}>
                  {PACING_MODES.map((mode) => <option key={mode.value} value={mode.value}>{mode.label}</option>)}
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
                <p className="mt-1.5 text-[11px] leading-4 text-[#8B949E]">{activeImageProvider.mode}. {activeImageProvider.risk} No Runway, ElevenLabs, or video render APIs are called.</p>
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
              Generate Football Scene Package
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
                disabled={generatedImageCount === 0 || downloadingZip}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#30363D] bg-[#161B22] px-4 py-3 text-sm font-bold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {downloadingZip ? 'Packaging ZIP...' : 'Download Images ZIP'}
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
                  <p className="text-xs text-[#8B949E]">{packageData.scenes.length} scenes for {packageData.form.duration} using {packageData.metadata.template.name}</p>
                </div>
                <CopyButton text={packageText}>Copy Full Package</CopyButton>
              </div>

              <div className="mb-4 grid gap-3 md:grid-cols-3">
                <div className="rounded-lg border border-[#21262D] bg-[#0D1117] p-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">1-second hook</p>
                  <p className="mt-1 text-sm text-white">{packageData.scenes[0]?.retention.recommendedCut}</p>
                </div>
                <div className="rounded-lg border border-[#21262D] bg-[#0D1117] p-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Peak energy</p>
                  <p className="mt-1 text-sm text-white">{Math.max(...packageData.scenes.map((scene) => scene.retention.energyScore))}/100</p>
                </div>
                <div className="rounded-lg border border-[#21262D] bg-[#0D1117] p-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Replay loop</p>
                  <p className="mt-1 text-sm text-white">{packageData.scenes.at(-1)?.retention.replayLoop}</p>
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                {packageData.scenes.map((scene) => (
                  <article key={scene.number} className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
                    <div className="mb-3 space-y-3">
                      <div className="min-w-0">
                        <h3 className="font-bold text-white">Scene {scene.number}: {scene.label}</h3>
                        <p className="text-xs text-[#8B949E]">{scene.duration}s · scene{scene.number}.png</p>
                        <p className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-[#F0B429]">{scene.thumbnailText}</p>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-3">
                        <CopyButton text={scene.imagePrompt} className="w-full whitespace-nowrap">Copy Image Prompt</CopyButton>
                        <CopyButton text={scene.videoPrompt} className="w-full whitespace-nowrap">Copy I2V Prompt</CopyButton>
                        <button
                          type="button"
                          onClick={() => generateSceneImage(scene, true)}
                          disabled={sceneImages[scene.number]?.status === 'generating'}
                          className="inline-flex w-full items-center justify-center whitespace-nowrap rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
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
                        <p className="text-xs text-emerald-300">Generated by {sceneImages[scene.number].provider || imageProvider} ({sceneImages[scene.number].providerMode || activeImageProvider.mode}) as {sceneImages[scene.number].filename}</p>
                      )}
                      {sceneImages[scene.number]?.status === 'error' && (
                        <p className="text-xs leading-5 text-red-300">{sceneImages[scene.number].error || 'Provider failed or image was not generated.'}</p>
                      )}
                      <div className="rounded-lg border border-[#30363D] bg-[#010409] p-3">
                        <div className="flex flex-col gap-3">
                          <div>
                            <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Local motion preview</p>
                            <p className="mt-1 text-xs leading-5 text-[#8B949E]">Creates a short local football-edit MP4 from the approved still. No Runway, ElevenLabs, or paid credits.</p>
                          </div>
                          <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                            <Select
                              value={sceneMotionStyles[scene.number] || inferMotionPreset(scene)}
                              onChange={(event) => updateMotionStyle(scene, event.target.value)}
                              aria-label={`Motion preset for scene ${scene.number}`}
                            >
                              {MOTION_PRESETS.map((preset) => (
                                <option key={preset.value} value={preset.value}>{preset.label}</option>
                              ))}
                            </Select>
                            <button
                              type="button"
                              onClick={() => generateMotionPreview(scene)}
                              disabled={sceneMotionPreviews[scene.number]?.status === 'generating' || sceneImages[scene.number]?.status !== 'success'}
                              className="inline-flex items-center justify-center whitespace-nowrap rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {sceneMotionPreviews[scene.number]?.status === 'generating' ? 'Rendering Preview' : 'Preview Motion'}
                            </button>
                          </div>
                        </div>
                        {sceneMotionPreviews[scene.number]?.status === 'success' && (
                          <div className="mt-3 space-y-2">
                            <video
                              src={sceneMotionPreviews[scene.number].videoUrl}
                              controls
                              muted
                              playsInline
                              className="aspect-[9/16] w-full max-h-[420px] rounded-lg border border-[#30363D] bg-black object-cover"
                            />
                            <p className="text-xs text-emerald-300">
                              Local preview ready: {sceneMotionPreviews[scene.number].duration}s {motionPresetLabel(sceneMotionPreviews[scene.number].motionStyle)}. Manual approval is still required before final use.
                            </p>
                            <button
                              type="button"
                              onClick={() => approveLocalMotionClip(scene)}
                              className="inline-flex w-full items-center justify-center rounded-lg bg-[#238636] px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-[#2EA043]"
                            >
                              Approve Local Motion Clip
                            </button>
                          </div>
                        )}
                        {sceneMotionPreviews[scene.number]?.status === 'error' && (
                          <p className="mt-2 text-xs leading-5 text-red-300">{sceneMotionPreviews[scene.number].error || 'Local motion preview failed.'}</p>
                        )}
                      </div>
                      <div className="rounded-lg border border-[#30363D] bg-[#010409] p-3">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Scene clip decision</p>
                            <p className="mt-1 text-xs leading-5 text-[#8B949E]">Approve a local preview, regenerate the image, or upload an external clip. Nothing advances without approval.</p>
                          </div>
                          <div className="flex shrink-0 flex-wrap gap-2">
                            <input
                              ref={(node) => {
                                if (node) externalClipInputRefs.current[scene.number] = node;
                              }}
                              type="file"
                              accept="video/mp4,video/quicktime,video/webm"
                              className="hidden"
                              onChange={(event) => {
                                uploadExternalClip(scene, event.target.files?.[0]);
                                event.target.value = '';
                              }}
                            />
                            <button
                              type="button"
                              onClick={() => externalClipInputRefs.current[scene.number]?.click()}
                              className="inline-flex items-center justify-center whitespace-nowrap rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] transition-colors hover:border-[#58A6FF] hover:text-white"
                            >
                              Upload External Clip
                            </button>
                          </div>
                        </div>

                        {sceneClipDecisions[scene.number]?.videoUrl && (
                          <div className="mt-3 space-y-2">
                            {sceneClipDecisions[scene.number].source === 'external_upload' && (
                              <video
                                src={sceneClipDecisions[scene.number].videoUrl}
                                controls
                                muted
                                playsInline
                                className="aspect-[9/16] w-full max-h-[420px] rounded-lg border border-[#30363D] bg-black object-cover"
                              />
                            )}
                            {sceneClipDecisions[scene.number].source === 'external_upload' && sceneClipDecisions[scene.number].status !== 'approved' && (
                              <button
                                type="button"
                                onClick={() => approveExternalClip(scene)}
                                className="inline-flex w-full items-center justify-center rounded-lg bg-[#238636] px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-[#2EA043]"
                              >
                                Approve Uploaded Clip
                              </button>
                            )}
                          </div>
                        )}

                        <div className={`mt-3 rounded-lg border px-3 py-2 text-xs leading-5 ${
                          sceneClipDecisions[scene.number]?.status === 'approved'
                            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                            : sceneClipDecisions[scene.number]?.status === 'blocked'
                              ? 'border-red-500/30 bg-red-500/10 text-red-300'
                              : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                        }`}>
                          <span className="font-semibold">
                            {sceneClipDecisions[scene.number]?.status === 'approved'
                              ? `Approved: ${sceneClipDecisions[scene.number]?.source === 'external_upload' ? 'uploaded external clip' : 'local motion clip'}`
                              : 'Awaiting approval'}
                          </span>
                          <span className="block">
                            {sceneClipDecisions[scene.number]?.message || 'Choose one approved clip source for this scene before final stitching.'}
                          </span>
                          {sceneClipDecisions[scene.number]?.fileName && (
                            <span className="block text-[#C9D1D9]">File: {sceneClipDecisions[scene.number].fileName}</span>
                          )}
                        </div>
                      </div>
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
                      <div className="rounded-lg border border-[#30363D] bg-[#010409] p-3">
                        <p className="mb-2 text-xs font-bold uppercase tracking-wide text-[#8B949E]">Retention engine</p>
                        <div className="grid gap-2 text-xs leading-5 text-[#C9D1D9] sm:grid-cols-2">
                          <p><span className="font-semibold text-white">Energy:</span> {scene.retention.energyScore}/100</p>
                          <p><span className="font-semibold text-white">Caption density:</span> {scene.retention.captionDensityScore}/100</p>
                          <p><span className="font-semibold text-white">Arc:</span> {scene.retention.emotionalArc}</p>
                          <p><span className="font-semibold text-white">Cut:</span> {scene.retention.recommendedCut}</p>
                          <p><span className="font-semibold text-white">Transition:</span> {scene.retention.transition}</p>
                          <p><span className="font-semibold text-white">Beat:</span> {scene.retention.beatDrop}</p>
                          <p><span className="font-semibold text-white">Caption:</span> {scene.retention.captionPlacement}</p>
                          <p><span className="font-semibold text-white">Interrupt:</span> {scene.retention.patternInterrupt}</p>
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
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">Final Stitch</h2>
                  <p className="mt-1 text-xs leading-5 text-[#8B949E]">
                    Builds one local MP4 from approved scene clips with captions, a simple local music bed, and metadata. It never auto-posts.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={createFinalStitch}
                  disabled={!allScenesApproved || finalStitch.status === 'rendering'}
                  className="inline-flex shrink-0 items-center justify-center rounded-lg bg-[#238636] px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-[#2EA043] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {finalStitch.status === 'rendering' ? 'Stitching Final Video...' : 'Stitch Approved Clips'}
                </button>
              </div>

              <div className="mt-3 grid gap-3 md:grid-cols-3">
                <div className="rounded-lg border border-[#30363D] bg-[#010409] p-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Approved scenes</p>
                  <p className="mt-1 text-lg font-bold text-white">{approvedSceneCount}/{packageData.scenes.length}</p>
                </div>
                <div className="rounded-lg border border-[#30363D] bg-[#010409] p-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Audio</p>
                  <p className="mt-1 text-sm text-[#C9D1D9]">Local music bed, no ElevenLabs</p>
                </div>
                <div className="rounded-lg border border-[#30363D] bg-[#010409] p-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Publishing</p>
                  <p className="mt-1 text-sm text-[#C9D1D9]">Manual export only</p>
                </div>
              </div>

              {!allScenesApproved && (
                <p className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs leading-5 text-amber-300">
                  Final stitch is blocked until every scene has an approved local motion clip or approved uploaded clip.
                </p>
              )}
              {finalStitch.status === 'error' && (
                <p className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs leading-5 text-red-300">{finalStitch.error}</p>
              )}
              {finalStitch.status === 'success' && (
                <div className="mt-4 space-y-3">
                  {finalStitch.videoUrl ? (
                    <video
                      src={finalStitch.videoUrl}
                      controls
                      playsInline
                      className="aspect-[9/16] w-full max-h-[620px] rounded-lg border border-[#30363D] bg-black object-cover"
                    />
                  ) : (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-3 text-xs leading-5 text-amber-200">
                      <p className="font-semibold">Video generated, but browser preview fetch failed. Use direct download or check local HTTPS certificate.</p>
                      {finalStitch.previewFetchError && <p className="mt-1 text-amber-100/90">{finalStitch.previewFetchError}</p>}
                    </div>
                  )}
                  <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs leading-5 text-emerald-300">
                    <p className="font-semibold">Final local stitch ready. Nothing was posted.</p>
                    {finalStitch.previewFetchError && (
                      <p>Video generated, but browser preview fetch failed. Use direct download or check local HTTPS certificate.</p>
                    )}
                    <p>Generation ID: {finalStitch.generationId || 'n/a'}</p>
                    <p>Run ID: {finalStitch.runId || 'n/a'}</p>
                    <p>Video file: {finalStitch.videoFile || finalStitch.downloadUrl || 'n/a'}</p>
                    <p>Metadata file: {finalStitch.metadataFile || 'n/a'}</p>
                    {finalStitch.downloadUrl && (
                      <p>
                        Direct download:{' '}
                        <a
                          href={finalStitch.directDownloadUrl || finalStitch.downloadUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="font-semibold text-[#58A6FF] underline decoration-[#58A6FF]/40 underline-offset-2 hover:text-white"
                        >
                          Open MP4
                        </a>
                      </p>
                    )}
                    <p>Cost: ${Number(finalStitch.costs?.total_cost_usd || 0).toFixed(2)} | Runway credits: {finalStitch.costs?.runway_credits_used || 0} | ElevenLabs credits: {finalStitch.costs?.elevenlabs_credits_used || 0}</p>
                  </div>
                </div>
              )}
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
              {Object.entries(packageData.metadata).filter(([platform]) => platform !== 'template').map(([platform, data]) => (
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

            <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
              <div className="mb-4">
                <h2 className="text-lg font-bold text-white">Performance Intelligence</h2>
                <p className="text-xs text-[#8B949E]">Log results after posting and use winners/losers to tune football topics, templates, teams, and platforms.</p>
              </div>

              <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
                <div className="space-y-3 rounded-lg border border-[#30363D] bg-[#010409] p-3">
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                    <Field label="Platform">
                      <Select value={performanceForm.platform} onChange={(e) => updatePerformanceField('platform', e.target.value)}>
                        {PLATFORMS.filter((platform) => platform !== 'All').map((platform) => <option key={platform}>{platform}</option>)}
                        <option>Facebook Reels</option>
                      </Select>
                    </Field>
                    <Field label="Posting time">
                      <TextInput type="datetime-local" value={performanceForm.postingTime} onChange={(e) => updatePerformanceField('postingTime', e.target.value)} />
                    </Field>
                    <Field label="Views">
                      <TextInput type="number" min="0" value={performanceForm.views} onChange={(e) => updatePerformanceField('views', e.target.value)} />
                    </Field>
                    <Field label="Likes">
                      <TextInput type="number" min="0" value={performanceForm.likes} onChange={(e) => updatePerformanceField('likes', e.target.value)} />
                    </Field>
                    <Field label="Comments">
                      <TextInput type="number" min="0" value={performanceForm.comments} onChange={(e) => updatePerformanceField('comments', e.target.value)} />
                    </Field>
                    <Field label="Shares">
                      <TextInput type="number" min="0" value={performanceForm.shares} onChange={(e) => updatePerformanceField('shares', e.target.value)} />
                    </Field>
                    <Field label="Subscribers gained">
                      <TextInput type="number" min="0" value={performanceForm.subscribers} onChange={(e) => updatePerformanceField('subscribers', e.target.value)} />
                    </Field>
                  </div>
                  <Field label="Retention notes">
                    <TextArea rows={3} value={performanceForm.retentionNotes} onChange={(e) => updatePerformanceField('retentionNotes', e.target.value)} placeholder="Where did viewers likely stay or drop?" />
                  </Field>
                  <Field label="Replayability notes">
                    <TextArea rows={3} value={performanceForm.replayabilityNotes} onChange={(e) => updatePerformanceField('replayabilityNotes', e.target.value)} placeholder="Did the ending invite replay or comments?" />
                  </Field>
                  <button
                    type="button"
                    onClick={savePerformanceLog}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#238636] px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-[#2EA043]"
                  >
                    Log Performance Result
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-4">
                    {[
                      ['Templates', performanceSummary.templates],
                      ['Topics', performanceSummary.topics],
                      ['Platforms', performanceSummary.platforms],
                      ['Teams/players', performanceSummary.teams],
                    ].map(([label, rows]) => (
                      <div key={label} className="rounded-lg border border-[#30363D] bg-[#010409] p-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">{label}</p>
                        {rows.length ? (
                          <div className="mt-2 space-y-2">
                            {rows.slice(0, 3).map((row) => (
                              <div key={row.key}>
                                <p className="truncate text-sm font-semibold text-white">{row.key}</p>
                                <p className="text-[11px] text-[#8B949E]">{row.posts} posts · {row.views} views · {row.comments} comments · {row.subscribers} subs</p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="mt-2 text-xs leading-5 text-[#8B949E]">No logs yet.</p>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="overflow-hidden rounded-lg border border-[#30363D]">
                    <div className="grid grid-cols-[1.2fr_0.8fr_0.6fr_0.6fr] gap-2 border-b border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-bold uppercase tracking-wide text-[#8B949E]">
                      <span>Video</span>
                      <span>Template</span>
                      <span>Result</span>
                      <span className="text-right">Score</span>
                    </div>
                    {performanceLogs.length ? performanceLogs.slice(0, 8).map((log) => (
                      <div key={log.id} className="grid grid-cols-[1.2fr_0.8fr_0.6fr_0.6fr] gap-2 border-b border-[#21262D] px-3 py-2 text-xs text-[#C9D1D9] last:border-b-0">
                        <div>
                          <p className="font-semibold text-white">{log.eventTopic}</p>
                          <p className="text-[#8B949E]">{log.platform} · {log.views} views · {log.comments} comments · +{log.subscribers} subs</p>
                        </div>
                        <span className="self-center truncate">{log.template}</span>
                        <span className={`self-center font-bold uppercase ${log.resultTag === 'winner' ? 'text-emerald-300' : log.resultTag === 'loser' ? 'text-red-300' : 'text-amber-300'}`}>{log.resultTag}</span>
                        <span className="self-center text-right font-semibold text-white">{log.score}</span>
                      </div>
                    )) : (
                      <div className="px-3 py-6 text-center text-sm text-[#8B949E]">No performance logs yet. Log the first posted football short after manual publishing.</div>
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}
