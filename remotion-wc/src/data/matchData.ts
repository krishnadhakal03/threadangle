// ── Match Configuration Layer ────────────────────────────────────────────────
// Central data source for all MatchdayHype compositions.
// Add a new key here to generate a new parameterized short-form video.

export type MatchId = 'brazil_vs_morocco' | 'japan_vs_netherlands';

// ── Utility ──────────────────────────────────────────────────────────────────

/** Convert a 6-digit hex color to CSS rgba() with a given alpha. */
export const hexToRgba = (hex: string, alpha: number): string => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// ── Shared types ──────────────────────────────────────────────────────────────

export interface TeamConfig {
  name: string;
  flag: string;
  /** Primary neon/accent hex — used for glow, labels, highlights */
  primaryColor: string;
  /** rgba CSS value for the flag card background */
  cardBackground: string;
  /** Color of the team name label rendered below the flag card */
  labelColor: string;
}

export interface H2HStat {
  label: string;
  /** Home team's value */
  home: number;
  /** Away team's value */
  away: number;
}

export interface GroupRow {
  pos: number;
  flag: string;
  name: string;
  mp: number;
  w: number;
  d: number;
  pts: number;
  /** Whether this row gets the neon accent highlight */
  highlight: boolean;
}

export interface MatchConfig {
  /** Path relative to /public — e.g. 'matchday/brazil_vs_morocco.jpg' */
  backgroundImage: string;
  /** Full pill text in the hero header — e.g. 'WORLD CUP 2026 · GROUP A' */
  tournamentPill: string;
  /** Short label for the Scene 3 standings badge — e.g. 'WORLD CUP 2026' */
  tournamentLabel: string;
  /** Large group title for Scene 3 — e.g. 'GROUP A' */
  groupTitle: string;
  /** Display date string — e.g. 'JUN 20, 2026' */
  matchDate: string;
  /** Display time string — e.g. '18:00 UTC' */
  matchTime: string;
  homeTeam: TeamConfig;
  awayTeam: TeamConfig;
  /** Full CSS linear-gradient string for the Scene 1 diagonal hero panel */
  heroGradient: string;
  /** Breaking news headline (Scene 1 card) */
  scene1Headline: string;
  /** Squad update subtext (Scene 1 alert badge) */
  scene1SubText: string;
  /** Single-string key stat for the Scene 2 highlight card */
  keyStatText: string;
  /** Total historical meetings — used in 'ALL-TIME RECORD · N MEETINGS' */
  h2hMeetings: number;
  /** Exactly 4 rows for the H2H grid (Component 2) */
  h2hStats: H2HStat[];
  /** Exactly 4 rows for the Group Stage leaderboard (Component 4) */
  groupStandings: GroupRow[];
  /** Formation badge label — e.g. '🇧🇷 BRAZIL · 4-3-3' */
  squadBadgeLabel: string;
  /** Formation string — e.g. '4-3-3' */
  formation: string;
  /** Manager surname — e.g. 'ANCELOTTI' */
  manager: string;
  /** Exactly 11 player names for the staggered squad grid (Component 3) */
  squadPlayers: string[];
  /** Scoreline prediction displayed in Scene 5 — e.g. '2-2' */
  prediction: string;
  /** Prediction subtitle — e.g. 'FULL TIME DRAW' */
  predictionSubLabel: string;
  /**
   * Audio clip paths relative to /public.
   * Clip durations are fixed: hook=87f, update=180f, stats=180f, predict=open-ended.
   * These boundaries are hardcoded in MatchdayHype — update both if clips change.
   */
  audioFiles: {
    hook: string;    // frames 0–87
    update: string;  // frames 87–267
    stats: string;   // frames 267–447
    predict: string; // frames 447–750
  };
}

// ── Match data registry ───────────────────────────────────────────────────────

export const MATCH_DATA: Record<MatchId, MatchConfig> = {

  // ── Brazil vs Morocco ──────────────────────────────────────────────────────
  brazil_vs_morocco: {
    backgroundImage:  'matchday/brazil_vs_morocco.jpg',
    tournamentPill:   'WORLD CUP 2026 · GROUP A',
    tournamentLabel:  'WORLD CUP 2026',
    groupTitle:       'GROUP A',
    matchDate:        'JUN 20, 2026',
    matchTime:        '18:00 UTC',

    homeTeam: {
      name:           'BRAZIL',
      flag:           '🇧🇷',
      primaryColor:   '#009C3B',
      cardBackground: 'rgba(0, 39, 118, 0.50)',
      labelColor:     '#FFFFFF',
    },
    awayTeam: {
      name:           'MOROCCO',
      flag:           '🇲🇦',
      primaryColor:   '#C8102E',
      cardBackground: 'rgba(200, 16, 46, 0.40)',
      labelColor:     '#FFFFFF',
    },

    heroGradient: 'linear-gradient(160deg, rgba(0,39,118,0.92) 0%, rgba(0,156,59,0.78) 55%, rgba(10,14,23,0.97) 100%)',

    scene1Headline: "ANCELOTTI'S BOMBSHELL",
    scene1SubText:  'NEYMAR OFFICIALLY OUT',
    keyStatText:    'BRAZIL UNBEATEN IN ALL 5 MEETINGS',

    h2hMeetings: 5,
    h2hStats: [
      { label: 'WINS',         home: 4,  away: 0 },
      { label: 'DRAWS',        home: 1,  away: 1 },
      { label: 'GOALS',        home: 11, away: 1 },
      { label: 'CLEAN SHEETS', home: 3,  away: 2 },
    ],

    groupStandings: [
      { pos: 1, flag: '🇧🇷', name: 'BRAZIL',  mp: 2, w: 2, d: 0, pts: 6, highlight: true  },
      { pos: 2, flag: '🇲🇦', name: 'MOROCCO', mp: 2, w: 1, d: 0, pts: 3, highlight: false },
      { pos: 3, flag: '🇺🇸', name: 'USA',     mp: 2, w: 0, d: 1, pts: 1, highlight: false },
      { pos: 4, flag: '🇭🇷', name: 'CROATIA', mp: 2, w: 0, d: 0, pts: 0, highlight: false },
    ],

    squadBadgeLabel: '🇧🇷 BRAZIL · 4-3-3',
    formation:       '4-3-3',
    manager:         'ANCELOTTI',
    squadPlayers: [
      'ALISSON', 'DANILO', 'MILITÃO', 'MARQUINHOS',
      'RENAN', 'CASEMIRO', 'PAQUETÁ', 'GERSON',
      'RODRYGO', 'G. JESUS', 'VINÍCIUS JR',
    ],

    prediction:          '2-2',
    predictionSubLabel:  'FULL TIME DRAW',

    audioFiles: {
      hook:    'matchday/voice_hook.mp3',
      update:  'matchday/voice_neymar.mp3',
      stats:   'matchday/voice_morocco.mp3',
      predict: 'matchday/voice_predict.mp3',
    },
  },

  // ── Japan vs Netherlands ───────────────────────────────────────────────────
  japan_vs_netherlands: {
    backgroundImage:  'matchday/japan_vs_netherlands.jpg',
    tournamentPill:   'WORLD CUP 2026 · GROUP E',
    tournamentLabel:  'WORLD CUP 2026',
    groupTitle:       'GROUP E',
    matchDate:        'JUN 22, 2026',
    matchTime:        '21:00 UTC',

    homeTeam: {
      name:           'JAPAN',
      flag:           '🇯🇵',
      primaryColor:   '#BC0018',
      cardBackground: 'rgba(188, 0, 24, 0.45)',
      labelColor:     '#FFFFFF',
    },
    awayTeam: {
      name:           'NETHERLANDS',
      flag:           '🇳🇱',
      primaryColor:   '#FF6600',
      cardBackground: 'rgba(255, 102, 0, 0.40)',
      labelColor:     '#FFFFFF',
    },

    heroGradient: 'linear-gradient(160deg, rgba(188,0,24,0.90) 0%, rgba(255,100,0,0.65) 55%, rgba(10,14,23,0.97) 100%)',

    scene1Headline: 'DO OR DIE FOR JAPAN',
    scene1SubText:  'DE JONG DOUBT FOR FIXTURE',
    keyStatText:    'NETHERLANDS LEAD THE ALL-TIME RECORD',

    h2hMeetings: 7,
    h2hStats: [
      { label: 'WINS',         home: 1, away: 4 },
      { label: 'DRAWS',        home: 2, away: 2 },
      { label: 'GOALS',        home: 8, away: 17 },
      { label: 'CLEAN SHEETS', home: 1, away: 3 },
    ],

    groupStandings: [
      { pos: 1, flag: '🇩🇪', name: 'GERMANY',     mp: 2, w: 2, d: 0, pts: 6, highlight: false },
      { pos: 2, flag: '🇯🇵', name: 'JAPAN',        mp: 2, w: 1, d: 0, pts: 3, highlight: true  },
      { pos: 3, flag: '🇳🇱', name: 'NETHERLANDS',  mp: 2, w: 0, d: 1, pts: 1, highlight: false },
      { pos: 4, flag: '🇸🇳', name: 'SENEGAL',      mp: 2, w: 0, d: 0, pts: 0, highlight: false },
    ],

    squadBadgeLabel: '🇯🇵 JAPAN · 4-2-3-1',
    formation:       '4-2-3-1',
    manager:         'MORIYASU',
    squadPlayers: [
      'GONDA', 'YAMANE', 'ITAKURA', 'TOMIYASU',
      'NAGATOMO', 'ENDO', 'TANAKA',
      'DOAN', 'KAMADA', 'MITOMA', 'UEDA',
    ],

    prediction:         '1-2',
    predictionSubLabel: 'NETHERLANDS WIN',

    audioFiles: {
      hook:    'matchday/voice_hook.mp3',
      update:  'matchday/voice_neymar.mp3',
      stats:   'matchday/voice_morocco.mp3',
      predict: 'matchday/voice_predict.mp3',
    },
  },
};
