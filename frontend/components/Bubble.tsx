/**
 * "The Bubble" component showing teams on the cusp of making the playoff.
 * Centered row layout matching the target design.
 */

import TeamLogo from './TeamLogo';
import { Ranking } from '../lib/types';

interface BubbleProps {
  rankings: Ranking[];
  className?: string;
}

export default function Bubble({ rankings, className = '' }: BubbleProps) {
  // Teams ranked 13-16 are "on the bubble"
  const bubbleTeams = rankings
    .filter((r) => r.rank >= 13 && r.rank <= 16)
    .slice(0, 4);

  if (bubbleTeams.length === 0) {
    return null;
  }

  return (
    <div className={`${className} flex items-center justify-center gap-6`}>
      <span className="text-sm font-semibold text-gray-700">The Bubble:</span>
      <div className="flex items-center gap-4">
        {bubbleTeams.map((ranking) => (
          <div
            key={ranking.team}
            className="flex flex-col items-center gap-1"
          >
            <div className="w-12 h-12 rounded-full border-2 border-gray-300 flex items-center justify-center bg-white hover:border-gray-400 transition-colors">
              <TeamLogo team={ranking.team} size="sm" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
