import React from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import { CTAScene }   from '../components/CTAScene';
import { PlayerCard } from '../components/PlayerCard';
import { TeamHook }   from '../components/TeamHook';

// ─── Germany data ──────────────────────────────────────────────────────────────
const GERMANY = {
  teamName:       'GERMANY',
  accentColor:    '#DD0000',
  secondaryColor: '#FFCE00',
  flagUrl:        'https://flagcdn.com/w320/de.png',
  groupId:        'A',

  player: {
    name:         'Jamal Musiala',
    displayName:  'MUSIALA',
    position:     'MID',
    club:         'Bayern Munich',
    goals:        22,
    caps:         54,
    clubGoals:    18,
    marketValue:  '200M EUR',
    ovr:          91,
    photoUrl:     staticFile('germany/musiala.jpg'),
    flagCode:     'de',
    countryCode:  'GER',
  },

  bgVideos: {
    hook:   staticFile('germany/hook.mp4'),
    player: staticFile('germany/player.mp4'),
    cta:    staticFile('germany/cta.mp4'),
  },
};

// ─── Composition ───────────────────────────────────────────────────────────────
export const GermanyShort: React.FC = () => {
  const frame = useCurrentFrame();

  // Dreamy-zoom: Hook exits zoom+fade, PlayerCard dissolves in (frames 140–160)
  const hookOpacity  = interpolate(frame, [140, 160], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const hookScale    = interpolate(frame, [140, 160], [1, 1.15], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const playerEnter  = interpolate(frame, [140, 160], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Dissolve: PlayerCard fades out, CTAScene fades in (frames 590–610)
  const playerExit   = interpolate(frame, [590, 610], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const ctaOpacity   = interpolate(frame, [590, 610], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const playerOpacity = Math.min(playerEnter, playerExit);

  return (
    <AbsoluteFill style={{ backgroundColor: '#0D0D14' }}>
      <Audio src={staticFile('football_hype.mp3')} volume={0.25} />

      {/* Scene 1: TeamHook with dreamy-zoom exit */}
      <AbsoluteFill style={{
        opacity: hookOpacity,
        transform: `scale(${hookScale})`,
        transformOrigin: 'center center',
      }}>
        <Sequence durationInFrames={165}>
          <TeamHook
            teamName={GERMANY.teamName}
            flagUrl={GERMANY.flagUrl}
            groupId={GERMANY.groupId}
            accentColor={GERMANY.accentColor}
            bgVideoPath={GERMANY.bgVideos.hook}
          />
        </Sequence>
      </AbsoluteFill>

      {/* Scene 2: PlayerCard with dissolve in/out */}
      <AbsoluteFill style={{ opacity: playerOpacity }}>
        <Sequence from={140} durationInFrames={475}>
          <PlayerCard
            name={GERMANY.player.name}
            displayName={GERMANY.player.displayName}
            position={GERMANY.player.position}
            club={GERMANY.player.club}
            goals={GERMANY.player.goals}
            caps={GERMANY.player.caps}
            clubGoals={GERMANY.player.clubGoals}
            marketValue={GERMANY.player.marketValue}
            ovr={GERMANY.player.ovr}
            accentColor={GERMANY.accentColor}
            secondaryColor={GERMANY.secondaryColor}
            bgVideoPath={GERMANY.bgVideos.player}
            photoUrl={GERMANY.player.photoUrl}
            flagCode={GERMANY.player.flagCode}
            countryCode={GERMANY.player.countryCode}
          />
        </Sequence>
      </AbsoluteFill>

      {/* Scene 3: CTAScene with dissolve in */}
      <AbsoluteFill style={{ opacity: ctaOpacity }}>
        <Sequence from={590} durationInFrames={310}>
          <CTAScene
            teamName={GERMANY.teamName}
            accentColor={GERMANY.secondaryColor}
            bgVideoPath={GERMANY.bgVideos.cta}
          />
        </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
