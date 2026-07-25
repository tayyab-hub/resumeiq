import { scoreBand } from '@/utilities/score';
import { cn } from '@/utilities/format';

/**
 * The headline score.
 *
 * Colour is never the only signal: the numeric value and the band label are
 * always shown, so the meaning survives for a colour-blind reader or a
 * black-and-white print.
 */
export function ScoreGauge({ score, size = 168 }: { score: number; size?: number }) {
  const band = scoreBand(score);
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - Math.min(100, Math.max(0, score)) / 100);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label={`Overall match score ${score} out of 100. ${band.label}.`}
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={band.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            className="transition-[stroke-dashoffset] duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('text-4xl font-semibold tabular-nums', band.text)}>{score}</span>
          <span className="text-xs font-medium uppercase tracking-wide text-ink-400">
            out of 100
          </span>
        </div>
      </div>
      <p className={cn('text-sm font-semibold', band.text)}>{band.label}</p>
    </div>
  );
}
