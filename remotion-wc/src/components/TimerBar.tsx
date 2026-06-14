import React from 'react';
import { useCurrentFrame, interpolate, interpolateColors } from 'remotion';

interface TimerBarProps {
  durationFrames?: number;
  startFrame?: number;
  height?: number;
  borderRadius?: number;
  fps?: number;
}

export const TimerBar: React.FC<TimerBarProps> = ({
  durationFrames = 300,
  startFrame = 0,
  height = 12,
  borderRadius = 6,
  fps = 30,
}) => {
  const frame = useCurrentFrame();

  const elapsed = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const width = interpolate(elapsed, [0, 1], [100, 0]);

  const color = interpolateColors(elapsed, [0, 0.5, 0.8, 1], [
    '#22C55E',
    '#F97316',
    '#EF4444',
    '#EF4444',
  ]);

  // Discrete zone glow — matches spec exactly
  const glowColor = elapsed < 0.5 ? '#22C55E' : elapsed < 0.8 ? '#F97316' : '#EF4444';
  const glow = `0 0 20px ${glowColor}`;

  const secondsLeft = Math.max(0, Math.ceil((1 - elapsed) * durationFrames / fps));

  return (
    <div style={{ width: '100%' }}>
      {/* Countdown label — right-aligned, color tracks bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          paddingRight: 40,
          paddingBottom: 6,
        }}
      >
        <span
          style={{
            fontSize: 48,
            fontWeight: 700,
            color,
            fontFamily: "'Oswald', 'Impact', sans-serif",
            lineHeight: 1,
            textShadow: glow,
          }}
        >
          {secondsLeft}
        </span>
      </div>

      {/* Track — flat rectangle, no overflow clip so right-radius shows on bar */}
      <div
        style={{
          width: '100%',
          height,
          backgroundColor: 'rgba(255,255,255,0.1)',
          borderRadius: 0,
        }}
      >
        {/* Bar — rounded right tip only, consumed left-to-right */}
        <div
          style={{
            width: `${width}%`,
            height: '100%',
            backgroundColor: color,
            borderRadius: `0 ${borderRadius}px ${borderRadius}px 0`,
            boxShadow: glow,
          }}
        />
      </div>
    </div>
  );
};
