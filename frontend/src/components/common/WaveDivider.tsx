import React from 'react';

interface WaveDividerProps {
  fillColor?: string; // e.g. '#edf5fa' or '#ffffff' or 'fill-sagar-canvas'
  secondaryFill?: string;
  height?: number;
  flip?: boolean;
  className?: string;
}

export const WaveDivider: React.FC<WaveDividerProps> = ({
  fillColor = '#edf5fa',
  secondaryFill = 'rgba(224, 242, 254, 0.45)', // powder blue
  height = 56,
  flip = false,
  className = '',
}) => {
  return (
    <div
      className={`w-full overflow-hidden leading-none select-none pointer-events-none ${
        flip ? 'rotate-180 -mb-1' : '-mt-1'
      } ${className}`}
      aria-hidden="true"
    >
      <svg
        className="relative block w-full"
        style={{ height: `${height}px` }}
        viewBox="0 0 1440 120"
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Layer 1: Background organic wave */}
        <path
          d="M0,32L60,42.7C120,53,240,75,360,74.7C480,75,600,53,720,48C840,43,960,53,1080,64C1200,75,1320,85,1380,90.7L1440,96L1440,120L1380,120C1320,120,1200,120,1080,120C960,120,840,120,720,120C600,120,480,120,360,120C240,120,120,120,60,120L0,120Z"
          fill={secondaryFill}
        />
        {/* Layer 2: Foreground crisp crest wave */}
        <path
          d="M0,64L48,69.3C96,75,192,85,288,80C384,75,480,53,576,48C672,43,768,53,864,64C960,75,1056,85,1152,80C1248,75,1344,53,1392,42.7L1440,32L1440,120L1392,120C1344,120,1248,120,1152,120C1056,120,960,120,864,120C768,120,672,120,576,120C480,120,384,120,288,120C192,120,96,120,48,120L0,120Z"
          fill={fillColor}
        />
      </svg>
    </div>
  );
};
