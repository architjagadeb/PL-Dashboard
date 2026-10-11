import { useMemo, useState } from 'react';
import { ClubFilter } from './components/ClubFilter';
import { Hero } from './components/Hero';
import { MinutesSlider } from './components/MinutesSlider';
import { PlayerDetailDrawer } from './components/PlayerDetailDrawer';
import { PlayerGrid } from './components/PlayerGrid';
import { PositionTabs, type PositionTabValue } from './components/PositionTabs';
import { SearchBar } from './components/SearchBar';
import { usePlayers } from './hooks/usePlayers';
import type { Player } from './types';

export default function App() {
  const { players, meta, loading, error } = usePlayers();

  // Filter state
  const [selectedPosition, setSelectedPosition] = useState<PositionTabValue>('all');
  const [selectedClub, setSelectedClub] = useState<string>('all');
  const [minMinutes, setMinMinutes] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Selected player for detail scouting drawer
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);

  // Extract unique clubs sorted alphabetically
  const uniqueClubs = useMemo(() => {
    const clubsSet = new Set<string>();
    players.forEach((p) => {
      if (p.club) clubsSet.add(p.club);
    });
    return Array.from(clubsSet).sort((a, b) => a.localeCompare(b));
  }, [players]);

  // Compute max minutes from dataset
  const maxMinutesInDataset = useMemo(() => {
    if (players.length === 0) return 3420;
    const max = Math.max(...players.map((p) => p.minutes ?? 0));
    // round up to next multiple of 90
    return Math.ceil(max / 90) * 90;
  }, [players]);

  // Counts per position tab
  const positionCounts = useMemo(() => {
    const counts: Record<PositionTabValue, number> = {
      all: players.length,
      forward: 0,
      midfielder: 0,
      defender: 0,
      goalkeeper: 0,
    };

    players.forEach((p) => {
      if (p.position_group && counts[p.position_group] !== undefined) {
        counts[p.position_group]++;
      }
    });

    return counts;
  }, [players]);

  // Filtered player list
  const filteredPlayers = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return players.filter((player) => {
      // Position filter
      if (selectedPosition !== 'all' && player.position_group !== selectedPosition) {
        return false;
      }

      // Club filter
      if (selectedClub !== 'all' && player.club !== selectedClub) {
        return false;
      }

      // Minutes filter
      if ((player.minutes ?? 0) < minMinutes) {
        return false;
      }

      // Search query filter (matches name or club)
      if (query.length > 0) {
        const matchesName = player.name.toLowerCase().includes(query);
        const matchesClub = player.club.toLowerCase().includes(query);
        if (!matchesName && !matchesClub) {
          return false;
        }
      }

      return true;
    });
  }, [players, selectedPosition, selectedClub, minMinutes, searchQuery]);

  const handleResetFilters = () => {
    setSelectedPosition('all');
    setSelectedClub('all');
    setMinMinutes(0);
    setSearchQuery('');
  };

  const handlePlayerClick = (player: Player) => {
    setSelectedPlayer(player);
  };

  // Compound filter key to trigger grid cross-fade
  const filterKey = `${selectedPosition}-${selectedClub}-${minMinutes}-${searchQuery}`;

  return (
    <div className="min-h-screen relative z-10 px-4 sm:px-6 lg:px-8 pb-16 max-w-[1440px] mx-auto text-slate-900 dark:text-slate-100 font-sans">
      {/* Masthead Header */}
      <header className="pt-6 pb-4 border-b border-slate-200/80 dark:border-[#233142]/80 flex flex-col gap-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase text-pitch bg-emerald-500/10 dark:bg-emerald-500/15 border border-pitch/20">
            <span className="w-1.5 h-1.5 rounded-full bg-pitch" />
            <span>Premier League Scout</span>
          </div>

          <div className="text-xs font-mono text-slate-500 dark:text-slate-400">
            Season {meta?.season ?? '2025–26'} • {meta?.source ?? 'FBref / Sports Reference'}
          </div>
        </div>

        <div className="flex items-baseline justify-between flex-wrap gap-x-6 gap-y-2">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 flex items-center gap-2">
            PL Scout 25/26
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-pitch text-white tracking-normal font-sans">
              PRO
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-2xl">
            Style-based scouting dashboard with multi-dimensional per-90 metrics, PCA positioning, and cosine similarity matching.
          </p>
        </div>
      </header>

      {/* Hero Section */}
      <Hero
        playerCount={players.length}
        clubCount={uniqueClubs.length || 20}
        season={meta?.season ?? '2025–26'}
        loading={loading}
      />

      {/* Sticky Scouting Controls Bar */}
      <section
        id="scouting-controls"
        className="sticky top-0 z-30 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-3.5 mb-6 bg-white/90 dark:bg-[#121922]/90 backdrop-blur-md border-b border-slate-200 dark:border-[#233142] shadow-xs"
      >
        <div className="max-w-[1440px] mx-auto flex flex-col gap-3.5">
          {/* Controls Row 1: Position Tabs & Result Counter */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <PositionTabs
              value={selectedPosition}
              onChange={setSelectedPosition}
              counts={positionCounts}
            />

            <div className="flex items-center gap-3 text-xs font-semibold text-slate-600 dark:text-slate-400">
              <span className="mono-num px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-[#1a2330] border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200">
                <span className="font-bold text-pitch">{filteredPlayers.length}</span> / {players.length} players
              </span>

              {(selectedPosition !== 'all' || selectedClub !== 'all' || minMinutes > 0 || searchQuery !== '') && (
                <button
                  type="button"
                  onClick={handleResetFilters}
                  className="text-xs text-rose-500 hover:text-rose-600 dark:text-rose-400 dark:hover:text-rose-300 font-semibold cursor-pointer underline transition-colors"
                >
                  Reset filters
                </button>
              )}
            </div>
          </div>

          {/* Controls Row 2: Search, Club Filter, Minutes Slider */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 items-center">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
            />

            <ClubFilter
              clubs={uniqueClubs}
              selectedClub={selectedClub}
              onChange={setSelectedClub}
            />

            <MinutesSlider
              value={minMinutes}
              max={maxMinutesInDataset}
              onChange={setMinMinutes}
              step={90}
            />
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main>
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-10 h-10 border-4 border-pitch/30 border-t-pitch rounded-full animate-spin mb-4" />
            <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">
              Loading Premier League scouting database...
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="p-6 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 text-rose-800 dark:text-rose-200 text-center my-8">
            <div className="text-3xl mb-2">⚠️</div>
            <h2 className="text-lg font-bold text-rose-900 dark:text-rose-100">
              Failed to load player data
            </h2>
            <p className="text-sm mt-1 text-rose-700 dark:text-rose-300 max-w-md mx-auto">
              {error}
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs transition-colors cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* Success: Players Grid */}
        {!loading && !error && filteredPlayers.length > 0 && (
          <PlayerGrid
            players={filteredPlayers}
            filterKey={filterKey}
            onPlayerClick={handlePlayerClick}
          />
        )}

        {/* Empty State */}
        {!loading && !error && filteredPlayers.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 px-4 text-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-white/50 dark:bg-[#131b25]/50">
            <div className="w-14 h-14 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-2xl mb-4">
              🔍
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              No players found matching your criteria
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mt-1 mb-6">
              Try lowering the minutes played threshold, clearing your search query, or selecting a different position group.
            </p>
            <button
              type="button"
              onClick={handleResetFilters}
              className="px-4 py-2 rounded-lg bg-pitch hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              Reset All Filters
            </button>
          </div>
        )}
      </main>

      {/* Scouting Profile Detail Drawer */}
      <PlayerDetailDrawer
        player={selectedPlayer}
        allPlayers={players}
        onClose={() => setSelectedPlayer(null)}
        onSelectPlayer={(player) => setSelectedPlayer(player)}
      />
    </div>
  );
}
