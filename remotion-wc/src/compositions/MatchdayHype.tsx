import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  spring,
} from 'remotion';
import { loadFont } from '@remotion/google-fonts/LilitaOne';
import { useAudioData, visualizeAudioWaveform } from '@remotion/media-utils';
import { MATCH_DATA, MatchId, hexToRgba } from '../data/matchData';

const { fontFamily } = loadFont();
const SANS = 'system-ui, -apple-system, BlinkMacSystemFont, sans-serif';

// ── Global design constants (not team-specific) ───────────────────────────────
const YELLOW   = '#FEDD00';
const GOLD     = '#FFD700';
const MUTED    = '#8E8E93';
const DARK     = '#05120A';
const CARD_BG  = 'rgba(10, 14, 23, 0.85)';
const CARD_BDR = 'rgba(255, 255, 255, 0.15)';
const W        = 1080;
const H        = 1920;

// ── Base broadcast card ───────────────────────────────────────────────────────
const CARD: React.CSSProperties = {
  background: CARD_BG,
  border: `2px solid ${CARD_BDR}`,
  borderRadius: '20px',
  backdropFilter: 'blur(24px)',
};

// ── Timeline ──────────────────────────────────────────────────────────────────
const SCENE_DUR = 150;
const TRANS     = 15;

const EASE_OPTS = {
  extrapolateLeft:  'clamp' as const,
  extrapolateRight: 'clamp' as const,
  easing: (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
};
const CL = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };

// ── Kinetic captions (timing coupled to audio clip lengths — update together) ─
interface WordCaption { text: string; from: number; to: number }
const WORD_CAPTIONS: WordCaption[] = [
  // Scene 1 (0–150f)
  { text: 'BREAKING', from: 5,   to: 30  },
  { text: 'NEWS',     from: 30,  to: 55  },
  { text: 'NEYMAR',   from: 55,  to: 85  },
  { text: 'IS',       from: 85,  to: 105 },
  { text: 'OUT',      from: 105, to: 145 },
  // Scene 2 (150–300f)
  { text: 'HEAD',     from: 155, to: 178 },
  { text: 'TO',       from: 178, to: 198 },
  { text: 'HEAD',     from: 198, to: 222 },
  { text: 'STATS',    from: 222, to: 260 },
  { text: 'BRAZIL',   from: 260, to: 295 },
  // Scene 3 (300–450f)
  { text: 'GROUP',    from: 305, to: 338 },
  { text: 'A',        from: 338, to: 368 },
  { text: 'BRAZIL',   from: 368, to: 398 },
  { text: 'LEADS',    from: 398, to: 428 },
  { text: 'TABLE',    from: 428, to: 448 },
  // Scene 4 (450–600f)
  { text: 'STARTING', from: 455, to: 495 },
  { text: 'ELEVEN',   from: 495, to: 533 },
  { text: 'FOUR',     from: 533, to: 568 },
  { text: 'THREE',    from: 568, to: 598 },
  // Scene 5 (600–750f)
  { text: 'PREDICT',  from: 605, to: 638 },
  { text: 'TWO',      from: 638, to: 663 },
  { text: 'ALL',      from: 663, to: 688 },
  { text: 'DRAW',     from: 688, to: 720 },
  { text: 'COMMENT',  from: 720, to: 748 },
];

// ── Sub-components ────────────────────────────────────────────────────────────

interface FlagCardProps {
  emoji: string;
  label: string;
  cardBg: string;
  labelColor: string;
}
const FlagCard: React.FC<FlagCardProps> = ({ emoji, label, cardBg, labelColor }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
    <div style={{
      width: 140, height: 140,
      border: '4px solid #FFF',
      borderRadius: 16,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: cardBg,
      boxShadow: '0 8px 30px rgba(0,0,0,0.50)',
    }}>
      <span style={{ fontSize: 82, lineHeight: 1 }}>{emoji}</span>
    </div>
    <span style={{ fontFamily: SANS, fontSize: 26, fontWeight: 800, color: labelColor, letterSpacing: 4 }}>
      {label}
    </span>
  </div>
);

const VsBadge: React.FC = () => (
  <div style={{
    position: 'absolute', left: '50%', top: 70,
    transform: 'translate(-50%, -50%)',
    width: 88, height: 88, borderRadius: '50%',
    background: `linear-gradient(135deg, ${YELLOW}, #FFA500)`,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
    border: '3px solid #FFF',
    zIndex: 10,
  }}>
    <span style={{ fontFamily, fontSize: 28, fontWeight: 900, color: '#000' }}>VS</span>
  </div>
);

// ── Props ─────────────────────────────────────────────────────────────────────

export interface MatchdayHypeProps {
  matchId: MatchId;
}

// ── Component ─────────────────────────────────────────────────────────────────

export const MatchdayHype: React.FC<MatchdayHypeProps> = ({ matchId }) => {
  // ── Active match config ───────────────────────────────────────────────────
  const m          = MATCH_DATA[matchId];
  const homeColor  = m.homeTeam.primaryColor;
  const awayColor  = m.awayTeam.primaryColor;

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Page slide engine ─────────────────────────────────────────────────────
  const slide = (from: number, to: number, boundary: number) =>
    interpolate(frame, [boundary - TRANS, boundary + TRANS], [from, to], EASE_OPTS);

  const pageFloat =
    frame < SCENE_DUR     - TRANS ? 0 :
    frame < SCENE_DUR     + TRANS ? slide(0, 1, SCENE_DUR) :
    frame < SCENE_DUR * 2 - TRANS ? 1 :
    frame < SCENE_DUR * 2 + TRANS ? slide(1, 2, SCENE_DUR * 2) :
    frame < SCENE_DUR * 3 - TRANS ? 2 :
    frame < SCENE_DUR * 3 + TRANS ? slide(2, 3, SCENE_DUR * 3) :
    frame < SCENE_DUR * 4 - TRANS ? 3 :
    frame < SCENE_DUR * 4 + TRANS ? slide(3, 4, SCENE_DUR * 4) :
    4;

  const sceneX = (n: number) => (n - pageFloat) * W;

  const entrance = (sceneIdx: number, delay: number) => {
    const s = spring({
      frame: frame - sceneIdx * SCENE_DUR - delay,
      fps,
      config: { damping: 12, mass: 0.4 },
    });
    return {
      opacity: s,
      transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`,
    };
  };

  // ── Audio ──────────────────────────────────────────────────────────────────
  const audioHook    = useAudioData(staticFile(m.audioFiles.hook));
  const audioUpdate  = useAudioData(staticFile(m.audioFiles.update));
  const audioStats   = useAudioData(staticFile(m.audioFiles.stats));
  const audioPredict = useAudioData(staticFile(m.audioFiles.predict));

  // Frame offset within the currently-playing clip.
  // Boundaries match Sequence durations below — update both together.
  const audioFrame =
    frame < 87  ? frame :
    frame < 267 ? frame - 87  :
    frame < 447 ? frame - 267 :
                  frame - 447;

  const activeAudioData =
    frame < 87  ? audioHook    :
    frame < 267 ? audioUpdate  :
    frame < 447 ? audioStats   :
                  audioPredict;

  const waveform = activeAudioData
    ? visualizeAudioWaveform({
        audioData: activeAudioData,
        frame: audioFrame,
        numberOfSamples: 24,
        fps,
        windowInSeconds: 1 / fps,
      })
    : Array.from({ length: 24 }, () => 0.05);

  // ── Kinetic caption ────────────────────────────────────────────────────────
  const activeWord = WORD_CAPTIONS.find(c => frame >= c.from && frame < c.to) ?? null;
  const wordAge    = activeWord ? frame - activeWord.from : 0;
  const wordPop    = interpolate(wordAge, [0, 5], [1.18, 1.0], CL);

  // ── Squad springs — computed before JSX, one per player ───────────────────
  const squadSprings = m.squadPlayers.map((_, i) =>
    spring({
      frame: frame - 3 * SCENE_DUR - (10 + i * 5),
      fps,
      config: { damping: 14, mass: 0.5 },
    })
  );

  return (
    <AbsoluteFill style={{ backgroundColor: DARK, fontFamily, overflow: 'hidden' }}>

      {/* ── Cinematic background ───────────────────────────────────────────── */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 1 }}>
        <Img
          src={staticFile(m.backgroundImage)}
          style={{
            width: '100%', height: '100%', objectFit: 'cover',
            filter: 'blur(12px) brightness(0.25)',
            transform: `scale(${interpolate(frame, [0, 750], [1, 1.15], { extrapolateRight: 'clamp' })})`,
          }}
        />
      </div>

      {/* ════════════════════════════════════════════════════════════════════
          SCENE 1 (0–150f) — MATCHDAY BANNER  [Component 1]
      ════════════════════════════════════════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: 0, left: 0, width: W, height: H,
        overflow: 'hidden', transform: `translateX(${sceneX(0)}px)`, zIndex: 2,
      }}>
        {/* Diagonal hero */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 740,
          clipPath: 'polygon(0 0, 100% 0, 100% 85%, 0% 100%)',
          background: m.heroGradient,
          backdropFilter: 'blur(10px)',
          ...entrance(0, 0),
        }}>
          {/* Tournament pill */}
          <div style={{ position: 'absolute', top: 80, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
            <div style={{
              background: 'rgba(255,255,255,0.10)', border: '1px solid rgba(255,255,255,0.25)',
              borderRadius: 50, padding: '10px 44px',
            }}>
              <span style={{ fontFamily, fontSize: 24, color: '#FFF', letterSpacing: 6, fontWeight: 900 }}>
                {m.tournamentPill}
              </span>
            </div>
          </div>

          {/* Flag cards + VS badge */}
          <div style={{ position: 'absolute', top: 210, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
            <div style={{ position: 'relative', display: 'inline-flex', gap: 80, alignItems: 'flex-start' }}>
              <FlagCard
                emoji={m.homeTeam.flag}
                label={m.homeTeam.name}
                cardBg={m.homeTeam.cardBackground}
                labelColor={m.homeTeam.labelColor}
              />
              <VsBadge />
              <FlagCard
                emoji={m.awayTeam.flag}
                label={m.awayTeam.name}
                cardBg={m.awayTeam.cardBackground}
                labelColor={m.awayTeam.labelColor}
              />
            </div>
          </div>

          {/* Match date + time */}
          <div style={{
            position: 'absolute', bottom: 128, left: 0, right: 0,
            display: 'flex', justifyContent: 'center', gap: 40,
          }}>
            <span style={{ fontFamily: SANS, fontSize: 18, fontWeight: 700, color: 'rgba(255,255,255,0.60)', letterSpacing: 3 }}>
              📅 {m.matchDate}
            </span>
            <span style={{ fontFamily: SANS, fontSize: 18, fontWeight: 700, color: 'rgba(255,255,255,0.35)' }}>·</span>
            <span style={{ fontFamily: SANS, fontSize: 18, fontWeight: 700, color: 'rgba(255,255,255,0.60)', letterSpacing: 3 }}>
              🕕 {m.matchTime}
            </span>
          </div>
        </div>

        {/* Breaking news card */}
        <div style={{ position: 'absolute', top: 758, left: 32, right: 32, ...entrance(0, 15) }}>
          <div style={{
            ...CARD,
            padding: '28px 36px',
            boxShadow: `0 0 28px ${hexToRgba(homeColor, 0.18)}, 0 20px 40px rgba(0,0,0,0.5)`,
          }}>
            <div style={{ fontFamily: SANS, fontSize: 12, fontWeight: 800, color: '#FF3B30', letterSpacing: 5, marginBottom: 10 }}>
              BREAKING NEWS
            </div>
            <div style={{ fontFamily, fontSize: 52, fontWeight: 900, color: '#FFF', lineHeight: 1.05 }}>
              {m.scene1Headline}
            </div>
          </div>
        </div>

        {/* Squad update badge */}
        <div style={{ position: 'absolute', top: 1018, left: 32, right: 32, ...entrance(0, 25) }}>
          <div style={{
            ...CARD,
            padding: '26px 32px',
            border: '2px solid rgba(255,51,51,0.52)',
            boxShadow: '0 0 24px rgba(255,51,51,0.16), 0 20px 40px rgba(0,0,0,0.5)',
            display: 'flex', alignItems: 'center', gap: 24,
          }}>
            <span style={{ fontSize: 50, lineHeight: 1, flexShrink: 0 }}>❌</span>
            <div>
              <div style={{ fontFamily: SANS, fontSize: 12, fontWeight: 800, color: MUTED, letterSpacing: 4, marginBottom: 6 }}>
                SQUAD UPDATE
              </div>
              <div style={{ fontFamily: SANS, fontSize: 34, fontWeight: 800, color: '#FFF', lineHeight: 1.15 }}>
                {m.scene1SubText}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════
          SCENE 2 (150–300f) — HEAD-TO-HEAD CARD  [Component 2]
      ════════════════════════════════════════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: 0, left: 0, width: W, height: H,
        overflow: 'hidden', transform: `translateX(${sceneX(1)}px)`, zIndex: 2,
      }}>
        {/* Header card */}
        <div style={{ position: 'absolute', top: 120, left: 32, right: 32, ...entrance(1, 0) }}>
          <div style={{
            ...CARD,
            padding: '30px 36px',
            boxShadow: `0 0 28px ${hexToRgba(homeColor, 0.14)}, 0 20px 40px rgba(0,0,0,0.5)`,
          }}>
            {/* Tri-color bar using both team colors */}
            <div style={{
              height: 4, borderRadius: 2, marginBottom: 22,
              background: `linear-gradient(90deg, ${homeColor}, ${YELLOW}, ${awayColor})`,
            }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 60, lineHeight: 1 }}>{m.homeTeam.flag}</span>
                <span style={{ fontFamily, fontSize: 20, fontWeight: 900, color: homeColor, letterSpacing: 3 }}>
                  {m.homeTeam.name}
                </span>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily, fontSize: 42, fontWeight: 900, color: '#FFF', letterSpacing: 3 }}>HEAD TO HEAD</div>
                <div style={{ fontFamily: SANS, fontSize: 13, fontWeight: 800, color: MUTED, letterSpacing: 3, marginTop: 6 }}>
                  ALL-TIME RECORD · {m.h2hMeetings} MEETINGS
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 60, lineHeight: 1 }}>{m.awayTeam.flag}</span>
                <span style={{ fontFamily, fontSize: 20, fontWeight: 900, color: awayColor, letterSpacing: 3 }}>
                  {m.awayTeam.name}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Stat pill rows */}
        <div style={{ position: 'absolute', top: 430, left: 32, right: 32 }}>
          {m.h2hStats.map((row, i) => {
            const homeWins = row.home > row.away;
            const awayWins = row.away > row.home;
            const s = spring({
              frame: frame - SCENE_DUR - (20 + i * 6),
              fps,
              config: { damping: 12, mass: 0.4 },
            });
            return (
              <div key={row.label} style={{
                background: 'rgba(255,255,255,0.03)',
                height: 64,
                marginBottom: 12,
                borderRadius: 12,
                display: 'flex',
                alignItems: 'center',
                padding: '0 20px',
                border: '1px solid rgba(255,255,255,0.06)',
                opacity: s,
                transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)`,
              }}>
                {/* Home metric */}
                <div style={{ flex: 1 }}>
                  {homeWins ? (
                    <span style={{
                      display: 'inline-block', padding: '4px 18px',
                      background: GOLD, borderRadius: 6,
                      fontFamily: SANS, fontSize: 24, fontWeight: 800, color: '#000',
                    }}>
                      {row.home}
                    </span>
                  ) : (
                    <span style={{ fontFamily: SANS, fontSize: 24, fontWeight: 800, color: '#FFF' }}>
                      {row.home}
                    </span>
                  )}
                </div>
                {/* Center label */}
                <div style={{
                  fontSize: 14, color: MUTED, fontWeight: 800,
                  width: 120, textAlign: 'center' as const,
                  fontFamily: SANS, letterSpacing: 2,
                }}>
                  {row.label}
                </div>
                {/* Away metric */}
                <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                  {awayWins ? (
                    <span style={{
                      display: 'inline-block', padding: '4px 18px',
                      background: GOLD, borderRadius: 6,
                      fontFamily: SANS, fontSize: 24, fontWeight: 800, color: '#000',
                    }}>
                      {row.away}
                    </span>
                  ) : (
                    <span style={{ fontFamily: SANS, fontSize: 24, fontWeight: 800, color: '#FFF' }}>
                      {row.away}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Key stat highlight card */}
        <div style={{ position: 'absolute', top: 762, left: 32, right: 32, ...entrance(1, 42) }}>
          <div style={{
            ...CARD,
            padding: '24px 32px',
            border: `2px solid ${hexToRgba(homeColor, 0.38)}`,
            boxShadow: `0 0 20px ${hexToRgba(homeColor, 0.12)}`,
            display: 'flex', alignItems: 'center', gap: 20,
          }}>
            <span style={{ fontSize: 44, lineHeight: 1, flexShrink: 0 }}>🏆</span>
            <div>
              <div style={{ fontFamily: SANS, fontSize: 12, fontWeight: 800, color: MUTED, letterSpacing: 4, marginBottom: 6 }}>
                KEY STAT
              </div>
              <div style={{ fontFamily: SANS, fontSize: 26, fontWeight: 800, color: '#FFF', lineHeight: 1.2 }}>
                {m.keyStatText}
              </div>
            </div>
          </div>
        </div>

        {/* Footnote */}
        <div style={{ position: 'absolute', bottom: 260, left: 0, right: 0, display: 'flex', justifyContent: 'center', ...entrance(1, 52) }}>
          <span style={{ fontFamily: SANS, fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.22)', letterSpacing: 3 }}>
            SOURCE: FIFA OFFICIAL RECORDS
          </span>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════
          SCENE 3 (300–450f) — GROUP STAGE DISPLAY  [Component 4]
      ════════════════════════════════════════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: 0, left: 0, width: W, height: H,
        overflow: 'hidden', transform: `translateX(${sceneX(2)}px)`, zIndex: 2,
      }}>
        {/* Header */}
        <div style={{
          position: 'absolute', top: 120, left: 32, right: 32,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
          ...entrance(2, 0),
        }}>
          <div style={{
            background: 'rgba(254,221,0,0.10)', border: '2px solid rgba(254,221,0,0.28)',
            borderRadius: 50, padding: '10px 48px',
          }}>
            <span style={{ fontFamily: SANS, fontSize: 17, fontWeight: 800, color: YELLOW, letterSpacing: 6 }}>
              {m.tournamentLabel}
            </span>
          </div>
          <span style={{ fontFamily, fontSize: 70, fontWeight: 900, color: '#FFF', textAlign: 'center', letterSpacing: 2 }}>
            {m.groupTitle}
          </span>
          <span style={{ fontFamily: SANS, fontSize: 15, fontWeight: 700, color: MUTED, letterSpacing: 4 }}>
            CURRENT STANDINGS
          </span>
        </div>

        {/* Standings table */}
        <div style={{ position: 'absolute', top: 420, left: 32, right: 32 }}>
          {/* Column header pill */}
          <div style={{
            background: '#1C1C1E', height: 40, borderRadius: 8,
            display: 'flex', alignItems: 'center', padding: '0 20px', marginBottom: 10,
            ...entrance(2, 10),
          }}>
            {(['POS', 'TEAM', 'MP', 'W', 'D', 'PTS'] as const).map((col, ci) => (
              <span key={col} style={{
                fontFamily: SANS, fontSize: 12, fontWeight: 800, color: MUTED,
                letterSpacing: 2, textAlign: 'center' as const,
                flex: ci === 1 ? 1 : undefined,
                width: ci === 0 ? 48 : ci >= 2 ? 64 : undefined,
              }}>
                {col}
              </span>
            ))}
          </div>

          {/* Team rows */}
          {m.groupStandings.map((team, i) => {
            const s = spring({
              frame: frame - 2 * SCENE_DUR - (16 + i * 8),
              fps,
              config: { damping: 12, mass: 0.4 },
            });
            const rowStyle: React.CSSProperties = team.highlight
              ? {
                  background: hexToRgba(homeColor, 0.13),
                  border: `2px solid ${hexToRgba(homeColor, 0.44)}`,
                  boxShadow: `0 0 20px ${hexToRgba(homeColor, 0.11)}`,
                }
              : {
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.06)',
                };
            return (
              <div key={team.name} style={{
                ...rowStyle,
                height: 80, borderRadius: 14, display: 'flex', alignItems: 'center',
                padding: '0 20px', marginBottom: 10,
                opacity: s,
                transform: `translateX(${interpolate(s, [0, 1], [-50, 0])}px)`,
              }}>
                {/* Position */}
                <span style={{
                  fontFamily: SANS, fontSize: 20, fontWeight: 800,
                  color: team.highlight ? YELLOW : MUTED,
                  width: 48, textAlign: 'center' as const,
                }}>
                  {team.pos}
                </span>
                {/* Flag + name */}
                <div style={{ display: 'flex', gap: 12, alignItems: 'center', flex: 1 }}>
                  <span style={{ fontSize: 30, lineHeight: 1 }}>{team.flag}</span>
                  <span style={{
                    fontFamily: SANS, fontSize: 20, fontWeight: 800,
                    color: team.highlight ? '#FFF' : 'rgba(255,255,255,0.68)',
                    letterSpacing: 2,
                  }}>
                    {team.name}
                  </span>
                  {team.highlight && (
                    <div style={{
                      background: homeColor, borderRadius: 4, padding: '2px 10px',
                      fontFamily: SANS, fontSize: 11, fontWeight: 800, color: '#FFF', letterSpacing: 1,
                    }}>
                      QUALIFYING
                    </div>
                  )}
                </div>
                {/* MP */}
                <span style={{ fontFamily: SANS, fontSize: 18, fontWeight: team.highlight ? 800 : 700, color: team.highlight ? '#FFF' : 'rgba(255,255,255,0.42)', width: 64, textAlign: 'center' as const }}>
                  {team.mp}
                </span>
                {/* W */}
                <span style={{ fontFamily: SANS, fontSize: 18, fontWeight: team.highlight ? 800 : 700, color: team.highlight ? '#FFF' : 'rgba(255,255,255,0.42)', width: 64, textAlign: 'center' as const }}>
                  {team.w}
                </span>
                {/* D */}
                <span style={{ fontFamily: SANS, fontSize: 18, fontWeight: team.highlight ? 800 : 700, color: team.highlight ? '#FFF' : 'rgba(255,255,255,0.42)', width: 64, textAlign: 'center' as const }}>
                  {team.d}
                </span>
                {/* PTS */}
                <span style={{ fontFamily, fontSize: 22, fontWeight: 900, color: team.highlight ? YELLOW : 'rgba(255,255,255,0.52)', width: 64, textAlign: 'center' as const }}>
                  {team.pts}
                </span>
              </div>
            );
          })}
        </div>

        {/* Footnote */}
        <div style={{ position: 'absolute', bottom: 260, left: 0, right: 0, display: 'flex', justifyContent: 'center', ...entrance(2, 55) }}>
          <span style={{ fontFamily: SANS, fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.22)', letterSpacing: 3 }}>
            AFTER MATCHDAY 2
          </span>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════
          SCENE 4 (450–600f) — SQUAD LIST  [Component 3]
      ════════════════════════════════════════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: 0, left: 0, width: W, height: H,
        overflow: 'hidden', transform: `translateX(${sceneX(3)}px)`, zIndex: 2,
      }}>
        {/* Tactical grid overlay */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'linear-gradient(rgba(254,221,0,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(254,221,0,0.04) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
        }} />

        {/* Header */}
        <div style={{
          position: 'absolute', top: 100, left: 32, right: 32,
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
          ...entrance(3, 0),
        }}>
          <div style={{
            background: 'rgba(254,221,0,0.10)', border: '2px solid rgba(254,221,0,0.28)',
            borderRadius: 50, padding: '10px 48px',
          }}>
            <span style={{ fontFamily: SANS, fontSize: 17, fontWeight: 800, color: YELLOW, letterSpacing: 5 }}>
              {m.squadBadgeLabel}
            </span>
          </div>
          <span style={{ fontFamily, fontSize: 64, fontWeight: 900, color: '#FFF', textAlign: 'center', letterSpacing: 2 }}>
            STARTING XI
          </span>
        </div>

        {/* Formation + manager badge */}
        <div style={{ position: 'absolute', top: 370, left: 32, right: 32, ...entrance(3, 10) }}>
          <div style={{
            ...CARD,
            padding: '20px 36px',
            border: `2px solid ${hexToRgba(YELLOW, 0.28)}`,
            boxShadow: `0 0 22px ${hexToRgba(YELLOW, 0.09)}`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div>
              <div style={{ fontFamily: SANS, fontSize: 12, fontWeight: 800, color: MUTED, letterSpacing: 4, marginBottom: 4 }}>
                FORMATION
              </div>
              <div style={{ fontFamily, fontSize: 50, fontWeight: 900, color: '#FFF', lineHeight: 1, letterSpacing: 6 }}>
                {m.formation}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontFamily: SANS, fontSize: 12, fontWeight: 800, color: MUTED, letterSpacing: 4, marginBottom: 4 }}>
                MANAGER
              </div>
              <div style={{ fontFamily: SANS, fontSize: 30, fontWeight: 800, color: YELLOW, letterSpacing: 1 }}>
                {m.manager}
              </div>
            </div>
          </div>
        </div>

        {/* 2-column squad grid — one spring per player, cascading +5f */}
        <div style={{
          position: 'absolute', top: 560, left: 32, right: 32,
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16,
        }}>
          {m.squadPlayers.map((player, i) => {
            const s = squadSprings[i];
            const isLast = i === m.squadPlayers.length - 1;
            return (
              <div key={player} style={{
                opacity: s,
                transform: `translateY(${interpolate(s, [0, 1], [30, 0])}px)`,
                gridColumn: isLast ? '1 / -1' : 'auto',
              }}>
                <div style={{
                  background: 'rgba(255,255,255,0.06)',
                  padding: '14px 16px',
                  borderRadius: 8,
                  borderLeft: `5px solid ${homeColor}`,
                  display: 'flex', alignItems: 'center', gap: 14,
                }}>
                  <span style={{ fontFamily: SANS, fontSize: 11, fontWeight: 800, color: MUTED, minWidth: 20, textAlign: 'center' as const }}>
                    {i + 1}
                  </span>
                  <span style={{ fontFamily: SANS, fontSize: 16, fontWeight: 800, color: '#FFF', letterSpacing: 1 }}>
                    {player}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════
          SCENE 5 (600–750f) — PREDICTION BANNER  [Component 1 variant]
      ════════════════════════════════════════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: 0, left: 0, width: W, height: H,
        overflow: 'hidden', transform: `translateX(${sceneX(4)}px)`, zIndex: 2,
      }}>
        {/* Diagonal hero — gold accent (prediction-specific) */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 600,
          clipPath: 'polygon(0 0, 100% 0, 100% 85%, 0% 100%)',
          background: 'linear-gradient(160deg, rgba(10,14,23,0.98) 0%, rgba(40,30,0,0.88) 50%, rgba(254,221,0,0.22) 100%)',
          backdropFilter: 'blur(10px)',
          ...entrance(4, 0),
        }}>
          {/* Section label */}
          <div style={{ position: 'absolute', top: 70, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
            <div style={{
              background: 'rgba(254,221,0,0.12)', border: '1px solid rgba(254,221,0,0.35)',
              borderRadius: 50, padding: '10px 44px',
            }}>
              <span style={{ fontFamily: SANS, fontSize: 17, fontWeight: 800, color: YELLOW, letterSpacing: 6 }}>
                OUR PREDICTION
              </span>
            </div>
          </div>

          {/* Flag cards + VS badge — reuses same data, team colors on labels */}
          <div style={{ position: 'absolute', top: 180, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
            <div style={{ position: 'relative', display: 'inline-flex', gap: 80, alignItems: 'flex-start' }}>
              <FlagCard
                emoji={m.homeTeam.flag}
                label={m.homeTeam.name}
                cardBg={m.homeTeam.cardBackground}
                labelColor={homeColor}
              />
              <VsBadge />
              <FlagCard
                emoji={m.awayTeam.flag}
                label={m.awayTeam.name}
                cardBg={m.awayTeam.cardBackground}
                labelColor={awayColor}
              />
            </div>
          </div>
        </div>

        {/* Score prediction card */}
        <div style={{ position: 'absolute', top: 618, left: 32, right: 32, ...entrance(4, 10) }}>
          <div style={{
            ...CARD,
            padding: '40px 48px',
            border: '2px solid rgba(254,221,0,0.38)',
            boxShadow: '0 0 30px rgba(255,215,0,0.18), 0 25px 50px rgba(0,0,0,0.60)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
          }}>
            <span style={{ fontFamily: SANS, fontSize: 13, fontWeight: 800, color: MUTED, letterSpacing: 5 }}>
              THREADANGLE PREDICTION
            </span>
            <span style={{ fontFamily, fontSize: 128, fontWeight: 900, color: '#FFF', lineHeight: 1, textShadow: '0 0 40px rgba(254,221,0,0.50)' }}>
              {m.prediction}
            </span>
            <span style={{ fontFamily: SANS, fontSize: 22, fontWeight: 800, color: YELLOW, letterSpacing: 6 }}>
              {m.predictionSubLabel}
            </span>
          </div>
        </div>

        {/* CTA button */}
        <div style={{ position: 'absolute', top: 1040, left: 32, right: 32, ...entrance(4, 20) }}>
          <div style={{
            background: YELLOW, borderRadius: 20, padding: '26px 40px',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20,
            boxShadow: '0 10px 30px rgba(254,221,0,0.28)',
          }}>
            <span style={{ fontSize: 46, lineHeight: 1 }}>💬</span>
            <span style={{ fontFamily: SANS, fontSize: 34, fontWeight: 800, color: '#000', lineHeight: 1.1, letterSpacing: 1 }}>
              COMMENT YOUR SCORE!
            </span>
          </div>
        </div>

        {/* Scene progress dots */}
        <div style={{
          position: 'absolute', top: 1220, left: 0, right: 0,
          display: 'flex', justifyContent: 'center', gap: 14,
          ...entrance(4, 28),
        }}>
          {[0, 1, 2, 3, 4].map(i => (
            <div key={i} style={{
              width: i === 4 ? 36 : 12, height: 12, borderRadius: 6,
              backgroundColor: i === 4 ? YELLOW : 'rgba(255,255,255,0.25)',
            }} />
          ))}
        </div>
      </div>

      {/* ── Kinetic captions — bottom safe zone ────────────────────────────── */}
      <div style={{
        position: 'absolute', bottom: '180px', left: 0, right: 0,
        display: 'flex', justifyContent: 'center',
        zIndex: 100, pointerEvents: 'none',
      }}>
        {activeWord && (
          <div style={{
            background: 'rgba(0,0,0,0.85)', padding: '12px 24px',
            borderRadius: '50px', border: '1px solid rgba(255,255,255,0.15)',
            transform: `scale(${wordPop})`, boxShadow: '0 10px 40px rgba(0,0,0,0.6)',
          }}>
            <span style={{ fontFamily, fontSize: 70, fontWeight: 900, color: '#FFF', lineHeight: 1, display: 'inline-block' }}>
              {activeWord.text}
            </span>
          </div>
        )}
      </div>

      {/* ── Audio waveform — zIndex 99, bright yellow ──────────────────────── */}
      <div style={{
        position: 'absolute', bottom: 24, left: 48, right: 48, height: 60,
        display: 'flex', alignItems: 'flex-end', gap: 5,
        zIndex: 99, pointerEvents: 'none',
      }}>
        {waveform.map((amp, i) => (
          <div key={i} style={{
            flex: 1, height: `${Math.max(3, amp * 60)}px`,
            backgroundColor: YELLOW, borderRadius: 3,
            boxShadow: `0 0 6px rgba(254,221,0,${Math.min(1, amp * 1.5)})`,
          }} />
        ))}
      </div>

      {/* ── Audio sequences — matchday narration only ──────────────────────── */}
      <Sequence from={0} durationInFrames={87}>
        <Audio src={staticFile(m.audioFiles.hook)} volume={1.0} />
      </Sequence>
      <Sequence from={87} durationInFrames={180}>
        <Audio src={staticFile(m.audioFiles.update)} volume={1.0} />
      </Sequence>
      <Sequence from={267} durationInFrames={180}>
        <Audio src={staticFile(m.audioFiles.stats)} volume={1.0} />
      </Sequence>
      <Sequence from={447}>
        <Audio src={staticFile(m.audioFiles.predict)} volume={1.0} />
      </Sequence>

    </AbsoluteFill>
  );
};
