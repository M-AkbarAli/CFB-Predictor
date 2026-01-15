/**
 * Individual team slot in the bracket.
 * Slim row style matching the target design.
 */

import TeamLogo from '../TeamLogo';
import { PlayoffTeam } from '../../lib/types';

interface BracketSlotProps {
  team: PlayoffTeam | null;
  isBye?: boolean;
  className?: string;
}

export default function BracketSlot({
  team,
  isBye = false,
  className = '',
}: BracketSlotProps) {
  if (!team) {
    return (
      <div
        className={`${className} h-12 flex items-center justify-center text-gray-400 text-sm`}
      >
        TBD
      </div>
    );
  }

  return (
    <div
      className={`${className} h-12 flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded hover:border-gray-300 transition-colors`}
    >
      <span className="text-xs font-bold text-gray-600 w-6">
        #{team.seed}
      </span>
      <TeamLogo team={team.team} size="sm" />
      <span className="text-sm font-medium text-gray-900 flex-1 truncate">
        {team.team}
      </span>
      {team.is_auto_bid && (
        <span className="text-xs" title="Conference Champion">
          🏆
        </span>
      )}
    </div>
  );
}
