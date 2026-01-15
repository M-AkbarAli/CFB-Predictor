/**
 * Home page - Bracket-first "Playoff Projector" layout.
 */

'use client';

import { useState, useEffect } from 'react';
import Bracket from '../components/Bracket/Bracket';
import GameSelector from '../components/GameSelector/GameSelector';
import Bubble from '../components/Bubble';
import { getSeasonData, runSimulation } from '../lib/api';
import {
  SeasonDataResponse,
  SimulationResponse,
  SimulationRequest,
  Ranking,
  PlayoffTeam,
} from '../lib/types';
import { ErrorDisplay } from './error-handling';

const AVAILABLE_YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020];

export default function Home() {
  const [season, setSeason] = useState(2023);
  const [seasonData, setSeasonData] = useState<SeasonDataResponse | null>(
    null
  );
  const [simulationResults, setSimulationResults] =
    useState<SimulationResponse | null>(null);
  const [selectedOutcomes, setSelectedOutcomes] = useState<
    Record<string, string>
  >({});
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenarioExpanded, setScenarioExpanded] = useState(false);

  // Load season data on mount and when season changes
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      setSimulationResults(null); // Clear previous results
      try {
        const data = await getSeasonData(season);
        
        // Check if we got empty data
        if (data.games.length === 0 && data.teams.length === 0 && data.rankings.length === 0) {
          setError(
            `No data available for ${season}. This may be due to API access restrictions. ` +
            `Try selecting a different season (2014-2023) or check your API key permissions.`
          );
          setSeasonData(null);
        } else {
          setSeasonData(data);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load data';
        setError(errorMessage);
        
        // If it's a 401/403 error, show helpful message
        if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
          setError(
            `API authentication failed for ${season}. ` +
            `Your API key may not have access to ${season} data, or the key may be invalid. ` +
            `Try selecting a different season (2014-2023) or check your CFBD_API_KEY.`
          );
        }
        setSeasonData(null);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [season]);

  // Auto-run baseline simulation when season data loads
  useEffect(() => {
    const runBaselineSimulation = async () => {
      if (!seasonData || seasonData.games.length === 0) {
        return;
      }

      setSimulating(true);
      try {
        const request: SimulationRequest = {
          game_outcomes: {}, // Empty outcomes = baseline projection
          season,
          target_week: 15, // Use week 15 explicitly for baseline
        };

        const results = await runSimulation(request);
        setSimulationResults(results);
      } catch (err) {
        console.error('Baseline simulation failed:', err);
        // Don't set error here - let user see the page even if baseline fails
      } finally {
        setSimulating(false);
      }
    };

    runBaselineSimulation();
  }, [seasonData, season]);

  const handleSimulate = async () => {
    if (!seasonData) {
      setError('No season data available');
      return;
    }

    setSimulating(true);
    setError(null);

    try {
      const request: SimulationRequest = {
        game_outcomes: selectedOutcomes,
        season,
        target_week: 15, // Use week 15 for consistency
      };

      const results = await runSimulation(request);
      setSimulationResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setSimulating(false);
    }
  };

  const handleOutcomeChange = (gameId: string, winner: string | null) => {
    if (winner === null) {
      const newOutcomes = { ...selectedOutcomes };
      delete newOutcomes[gameId];
      setSelectedOutcomes(newOutcomes);
    } else {
      setSelectedOutcomes({ ...selectedOutcomes, [gameId]: winner });
    }
  };

  const rankings = simulationResults?.rankings || [];
  const playoffTeams = simulationResults?.playoff_teams || [];

  // Get upcoming games (games not yet played)
  const upcomingGames = (() => {
    if (!seasonData?.games) return [];
    
    const filtered = seasonData.games.filter((game: any) => {
      // Filter logic: games in future weeks or games without results
      const gameWeek = game.week || 0;
      const currentWeek = seasonData.current_week || 0;
      const hasResult = game.team_won !== null && game.team_won !== undefined;
      return gameWeek > currentWeek || !hasResult;
    });
    
    return filtered.map((g: any) => ({
      game_id:
        g.game_id ||
        `${g.team || ''}_${g.opponent || ''}_${g.week || 0}_${g.season || season}`,
      team1: g.team || '',
      team2: g.opponent || '',
      week: g.week || 0,
      date: g.date,
    }));
  })();

  return (
    <main className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        {/* Centered card container */}
        <div className="max-w-5xl mx-auto bg-white rounded-lg shadow-lg p-8">
          {/* Year tabs */}
          <div className="flex items-center justify-center gap-2 mb-6 border-b border-gray-200 pb-4">
            {AVAILABLE_YEARS.map((year, idx) => (
              <div key={year} className="flex items-center">
                <button
                  onClick={() => setSeason(year)}
                  className={`px-3 py-1 text-sm font-medium transition-colors ${
                    season === year
                      ? 'text-gray-900 font-bold border-b-2 border-gray-900'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {year}
                </button>
                {idx < AVAILABLE_YEARS.length - 1 && (
                  <span className="text-gray-300 mx-1">|</span>
                )}
              </div>
            ))}
          </div>

          {/* Title */}
          <div className="text-center mb-4">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {season} Playoff Projector
            </h1>
            <p className="text-sm text-gray-600">
              Prior weeks and years may have ranking differences due to playoff criteria adjustments and conference realignment.
            </p>
          </div>

          {/* Dropdown selectors */}
          <div className="flex items-center justify-center gap-4 mb-8">
            <div className="relative">
              <select className="appearance-none bg-white border border-gray-300 rounded px-4 py-2 pr-8 text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option>5 Conference Champ Bids ✓</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                </svg>
              </div>
            </div>
            <div className="relative">
              <select className="appearance-none bg-white border border-gray-300 rounded px-4 py-2 pr-8 text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option>12 Team Playoff ✓</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Error display */}
          {error && (
            <div className="mb-6">
              <ErrorDisplay
                error={error}
                onDismiss={() => setError(null)}
              />
            </div>
          )}

          {/* Loading state */}
          {(loading || simulating) && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-center">
              {loading ? 'Loading season data...' : 'Running simulation...'}
            </div>
          )}

          {/* Bracket - always show if we have results */}
          {simulationResults && playoffTeams.length > 0 && (
            <div className="mb-8">
              <Bracket
                playoffTeams={playoffTeams}
                matchups={simulationResults.matchups}
              />
            </div>
          )}

          {/* Skeleton loader while waiting for baseline simulation */}
          {!loading && seasonData && seasonData.games.length > 0 && !simulationResults && (simulating || !seasonData) && (
            <div className="mb-8 p-12 text-center text-gray-400">
              <p>Generating baseline projection...</p>
            </div>
          )}

          {/* Empty state for no data - but keep layout visible */}
          {!loading && seasonData && seasonData.games.length === 0 && !simulating && (
            <div className="mb-8 p-12 text-center text-gray-500">
              <p className="text-lg font-semibold mb-2">No Data Available</p>
              <p className="text-sm">
                No game data found for {season}. Try selecting a different season.
              </p>
            </div>
          )}

          {/* The Bubble */}
          {simulationResults && rankings.length > 0 && (
            <div className="mb-8">
              <Bubble rankings={rankings} />
            </div>
          )}

          {/* Scenario controls - collapsed by default */}
          <div className="border-t border-gray-200 pt-6">
            <button
              onClick={() => setScenarioExpanded(!scenarioExpanded)}
              className="w-full text-left flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div>
                <h3 className="font-semibold text-gray-900">Scenario</h3>
                <p className="text-sm text-gray-600">
                  {scenarioExpanded ? 'Hide game outcomes' : 'Edit game outcomes to see different projections'}
                </p>
              </div>
              <svg
                className={`w-5 h-5 text-gray-500 transition-transform ${
                  scenarioExpanded ? 'transform rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {scenarioExpanded && seasonData && seasonData.games.length > 0 && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <GameSelector
                  games={upcomingGames}
                  selectedOutcomes={selectedOutcomes}
                  onOutcomeChange={handleOutcomeChange}
                />
                <button
                  onClick={handleSimulate}
                  disabled={simulating}
                  className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {simulating ? 'Running Simulation...' : 'Run Simulation'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
