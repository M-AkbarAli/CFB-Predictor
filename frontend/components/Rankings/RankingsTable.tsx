/**
 * Rankings table component displaying Top 25 teams.
 */

import { Ranking } from '../../lib/types';
import TeamLogo from '../TeamLogo';

interface RankingsTableProps {
  rankings: Ranking[];
  playoffTeams?: Set<string>;
  className?: string;
}

export default function RankingsTable({
  rankings,
  playoffTeams = new Set(),
  className = '',
}: RankingsTableProps) {
  const top25 = rankings.slice(0, 25);

  return (
    <div className={`${className} overflow-x-auto`}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Rank
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Team
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Record
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              SOS
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Top 25 Wins
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Record Strength
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {top25.map((ranking) => {
            const isPlayoff = playoffTeams.has(ranking.team);
            return (
              <tr
                key={ranking.team}
                className={`${
                  isPlayoff ? 'bg-green-50' : ''
                } hover:bg-gray-50 transition-colors`}
              >
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm font-medium text-gray-900">
                    #{ranking.rank}
                  </span>
                  {isPlayoff && (
                    <span className="ml-2 text-xs text-green-600">✓</span>
                  )}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <TeamLogo team={ranking.team} size="sm" />
                    <span className="text-sm font-medium text-gray-900">
                      {ranking.team}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {ranking.wins !== undefined && ranking.losses !== undefined
                    ? `${ranking.wins}-${ranking.losses}`
                    : '—'}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {ranking.weighted_sos_score !== undefined
                    ? ranking.weighted_sos_score.toFixed(3)
                    : ranking.sos_score !== undefined
                    ? ranking.sos_score.toFixed(3)
                    : '—'}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {ranking.wins_vs_top25 ?? '—'}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {ranking.record_strength_score !== undefined
                    ? ranking.record_strength_score.toFixed(1)
                    : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
