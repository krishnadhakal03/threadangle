/**
 * ProgressBar — horizontal bar that fills left-to-right.
 * Adapted from progress-bars pattern; fully prop-driven.
 */
import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

export interface ProgressBarProps {
  /** Final fill level 0–1 */
  progress: number;
  color: string;
  width?: number;
  height?: number;
  /** Local frame to begin the fill animation (default 0) */
  startFrame?: number;
  /** Frames the fill animation takes (default 30) */
  animDuration?: number;
  /** Background track colour (default dark grey) */
  trackColor?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  color,
  width = 300,
  height = 6,
  startFrame = 0,
  animDuration = 30,
  trackColor = 'rgba(255,255,255,0.1)',
}) => {
  const frame      = useCurrentFrame();
  const localFrame = Math.max(0, frame - startFrame);

  const animatedFill = interpolate(localFrame, [0, animDuration], [0, progress], {
    extrapolateLeft:  'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: trackColor,
        borderRadius:    height / 2,
        overflow:        'hidden',
      }}
    >
      <div
        style={{
          width:           `${animatedFill * 100}%`,
          height:          '100%',
          backgroundColor: color,
          borderRadius:    height / 2,
          boxShadow:       `0 0 8px ${color}`,
        }}
      />
    </div>
  );
};
