/**
 * Main bracket visualization component.
 * Displays the 12-team playoff bracket with connecting lines.
 */

import { PlayoffTeam, BracketMatchup } from '../../lib/types';
import BracketSlot from './BracketSlot';

interface BracketProps {
  playoffTeams: PlayoffTeam[];
  matchups: BracketMatchup[];
  className?: string;
}

export default function Bracket({
  playoffTeams,
  matchups,
  className = '',
}: BracketProps) {
  // Organize teams by seed
  const teamsBySeed = new Map<number, PlayoffTeam>();
  playoffTeams.forEach((team) => {
    teamsBySeed.set(team.seed, team);
  });

  // Get first-round matchups (excluding byes)
  const firstRoundGames = matchups
    .filter((m) => m.round === 'First Round' && m.team2 !== null && m.team2_seed !== null)
    .sort((a, b) => (a.team1_seed || 0) - (b.team1_seed || 0));

  // Seeds 1-4 get byes (ordered: 1, 4, 2, 3 for bracket layout - top half then bottom half)
  const byes = [
    teamsBySeed.get(1),  // Top half, left
    teamsBySeed.get(4), // Top half, right
    teamsBySeed.get(2), // Bottom half, left
    teamsBySeed.get(3), // Bottom half, right
  ].filter((team): team is PlayoffTeam => team !== undefined);

  // Organize first round games by bracket position
  // Format: 8v9 (plays 1), 5v12 (plays 4), 7v10 (plays 2), 6v11 (plays 3)
  const bracketGames = [
    { higher: 8, lower: 9, byeSeed: 1 },   // Winner plays seed 1
    { higher: 5, lower: 12, byeSeed: 4 },  // Winner plays seed 4
    { higher: 7, lower: 10, byeSeed: 2 },  // Winner plays seed 2
    { higher: 6, lower: 11, byeSeed: 3 },  // Winner plays seed 3
  ].map(({ higher, lower, byeSeed }) => {
    const game = firstRoundGames.find(
      (g) =>
        (g.team1_seed === higher && g.team2_seed === lower) ||
        (g.team1_seed === lower && g.team2_seed === higher)
    );
    return {
      higher: teamsBySeed.get(higher),
      lower: teamsBySeed.get(lower),
      byeSeed,
      game,
    };
  });

  return (
    <div className={`${className} relative`}>
      {/* Bracket container with SVG overlay for lines */}
      <div className="relative" style={{ minHeight: '480px' }}>
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none z-0"
          style={{ minHeight: '480px' }}
        >
          {/* Lines connecting first round to quarterfinals */}
          {bracketGames.map((bracketGame, idx) => {
            // Calculate positions
            const firstRoundX = 80; // Left column (first round)
            const quarterfinalX = 480; // Right column (byes)
            
            // First round game position (vertical center of the matchup)
            const firstRoundY = 50 + idx * 110;
            
            // Corresponding bye position
            const byeIndex = byes.findIndex(b => b?.seed === bracketGame.byeSeed);
            const byeY = 50 + byeIndex * 110;

            return (
              <g key={idx}>
                {/* Horizontal line from first round game to right */}
                <line
                  x1={firstRoundX + 180}
                  y1={firstRoundY}
                  x2={quarterfinalX - 15}
                  y2={firstRoundY}
                  stroke="#cbd5e1"
                  strokeWidth="2"
                />
                {/* Vertical line up/down to bye */}
                <line
                  x1={quarterfinalX - 15}
                  y1={firstRoundY}
                  x2={quarterfinalX - 15}
                  y2={byeY}
                  stroke="#cbd5e1"
                  strokeWidth="2"
                />
                {/* Horizontal line to bye */}
                <line
                  x1={quarterfinalX - 15}
                  y1={byeY}
                  x2={quarterfinalX}
                  y2={byeY}
                  stroke="#cbd5e1"
                  strokeWidth="2"
                />
              </g>
            );
          })}
        </svg>

        {/* Bracket content */}
        <div className="grid grid-cols-2 gap-16 relative z-10 px-8">
          {/* Left: First Round Matchups */}
          <div className="space-y-3">
            {bracketGames.map((bracketGame, idx) => (
              <div key={idx} className="space-y-1">
                <BracketSlot team={bracketGame.higher || null} />
                <BracketSlot team={bracketGame.lower || null} />
              </div>
            ))}
          </div>

          {/* Right: Seeds 1-4 with byes (quarterfinals) */}
          <div className="space-y-3">
            {byes.map((team) => (
              <div key={team.seed} className="flex items-center">
                <BracketSlot team={team} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
