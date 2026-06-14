/**
 * StatCounter — reusable animated stat (counting number + label).
 * Uses spring() so the count accelerates then eases at the target.
 * Works inside any Sequence; reads local frame via useCurrentFrame().
 */
import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

export interface StatCounterProps {
  label: string;
  value: number;
  color: string;
  /** Local frame at which the count-up begins (default 0) */
  startFrame?: number;
  /** Font size for the number (default 52) */
  fontSize?: number;
}

export const StatCounter: React.FC<StatCounterProps> = ({
  label,
  value,
  color,
  startFrame = 0,
  fontSize = 52,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const localFrame = Math.max(0, frame - startFrame);

  // Spring gives acceleration + ease: feels snappier than linear
  const countSpring = spring({
    frame: localFrame,
    fps,
    config: { damping: 200, stiffness: 80 },
  });
  const displayed = Math.round(interpolate(countSpring, [0, 1], [0, value]));

  // Label fades in after number settles (~80% through spring)
  const labelOpacity = interpolate(localFrame, [40, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtle pulse glow on the number
  const glow = 8 + Math.sin(frame * 0.2) * 4;

  return (
    <div style={{ textAlign: 'center' }}>
      <div
        style={{
          fontSize,
          fontWeight: 700,
          color,
          fontFamily: 'Arial Black, Arial, sans-serif',
          textShadow: `0 0 ${glow}px ${color}`,
          lineHeight: 1,
        }}
      >
        {displayed}
      </div>
      <div
        style={{
          opacity: labelOpacity,
          fontSize: 15,
          color: 'rgba(255,255,255,0.55)',
          fontFamily: 'Arial, sans-serif',
          letterSpacing: 2,
          marginTop: 6,
          textTransform: 'uppercase',
        }}
      >
        {label}
      </div>
    </div>
  );
};
