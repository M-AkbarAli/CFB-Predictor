/**
 * Game selector component for choosing game outcomes.
 */

'use client';

import { useState, useEffect } from 'react';

interface Game {
  game_id: string;
  team1: string;
  team2: string;
  week: number;
  date?: string;
}

interface GameSelectorProps {
  games: Game[];
  selectedOutcomes: Record<string, string>;
  onOutcomeChange: (gameId: string, winner: string | null) => void;
  className?: string;
}

export default function GameSelector({
  games,
  selectedOutcomes,
  onOutcomeChange,
  className = '',
}: GameSelectorProps) {
  // Group games by week
  const gamesByWeek = games.reduce((acc, game) => {
    const week = game.week || 0;
    if (!acc[week]) acc[week] = [];
    acc[week].push(game);
    return acc;
  }, {} as Record<number, Game[]>);

  const weeks = Object.keys(gamesByWeek)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div className={`${className} space-y-6`}>
      <h2 className="text-xl font-bold text-gray-900">Select Game Outcomes</h2>

      {weeks.map((week) => (
        <div key={week} className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-700 mb-3">
            Week {week}
          </h3>
          <div className="space-y-3">
            {gamesByWeek[week].map((game) => {
              const selectedWinner = selectedOutcomes[game.game_id] || null;

              return (
                <div
                  key={game.game_id}
                  className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1 flex items-center gap-3">
                    <button
                      onClick={() => onOutcomeChange(game.game_id, game.team1)}
                      className={`flex-1 p-2 rounded text-sm font-medium transition-colors ${
                        selectedWinner === game.team1
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                      }`}
                    >
                      {game.team1}
                    </button>
                    <span className="text-gray-400 font-bold">vs</span>
                    <button
                      onClick={() => onOutcomeChange(game.game_id, game.team2)}
                      className={`flex-1 p-2 rounded text-sm font-medium transition-colors ${
                        selectedWinner === game.team2
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                      }`}
                    >
                      {game.team2}
                    </button>
                  </div>
                  {selectedWinner && (
                    <button
                      onClick={() => onOutcomeChange(game.game_id, null)}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Clear
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
