/**
 * OVRCircle — SVG ring that draws itself clockwise over 30 frames.
 * Adapted from donut-chart pattern; works for any OVR/rating value.
 */
import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

export interface OVRCircleProps {
  ovr: number;
  /** Ring + label colour (usually the team's secondary/accent colour) */
  color: string;
  /** Pixel diameter of the whole SVG (default 200) */
  size?: number;
}

export const OVRCircle: React.FC<OVRCircleProps> = ({ ovr, color, size = 200 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const radius       = size * 0.38;
  const strokeWidth  = size * 0.042;
  const circumference = 2 * Math.PI * radius;

  const progress = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 200 },
  });
  const strokeDashoffset = interpolate(progress, [0, 1], [circumference, 0]);

  const cx = size / 2;
  const cy = size / 2;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
    >
      {/* Track ring */}
      <circle
        cx={cx} cy={cy} r={radius}
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth={strokeWidth}
      />
      {/* Animated fill ring */}
      <circle
        cx={cx} cy={cy} r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
      />
      {/* OVR number */}
      <text
        x={cx} y={cy - 4}
        textAnchor="middle"
        fill="white"
        fontSize={size * 0.19}
        fontWeight="700"
        fontFamily="Arial, sans-serif"
      >
        {ovr}
      </text>
      {/* OVR label */}
      <text
        x={cx} y={cy + size * 0.13}
        textAnchor="middle"
        fill={color}
        fontSize={size * 0.09}
        fontFamily="Arial, sans-serif"
        letterSpacing="2"
      >
        OVR
      </text>
    </svg>
  );
};
