import React, { useEffect, useState } from 'react';
import type { Player, PositionGroup } from '../types';

interface PlayerDetailDrawerProps {
  player: Player | null;
  allPlayers: Player[];
  onClose: () => void;
  onSelectPlayer: (player: Player) => void;
}

const DETAIL_STATS_KEYS: Record<PositionGroup, string[]> = {
  forward: [
    'goals',
    'assists',
    'goals_assists',
    'goals_per90',
    'assists_per90',
    'goals_assists_per90',
    'shots',
    'shots_per90',
    'shots_on_target',
    'shots_on_target_per90',
    'crosses_per90',
    'fouls_drawn_per90',
    'tackles_won_per90',
    'interceptions_per90',
    'yellow_cards',
  ],
  midfielder: [
    'goals_assists',
    'goals_assists_per90',
    'goals',
    'assists',
    'tackles_won',
    'tackles_won_per90',
    'interceptions',
    'interceptions_per90',
    'shots_per90',
    'crosses_per90',
    'fouls_committed_per90',
    'fouls_drawn_per90',
    'yellow_cards',
    'team_goals_on_pitch_per90',
    'team_goals_against_on_pitch_per90',
  ],
  defender: [
    'tackles_won',
    'tackles_won_per90',
    'interceptions',
    'interceptions_per90',
    'fouls_committed',
    'fouls_committed_per90',
    'fouls_drawn_per90',
    'team_goals_against_on_pitch_per90',
    'crosses_per90',
    'goals',
    'assists',
    'yellow_cards',
    'red_cards',
  ],
  goalkeeper: [
    'saves',
    'save_pct',
    'clean_sheets',
    'clean_sheet_pct',
    'goals_against',
    'goals_against_per90',
    'saves_per90',
    'shots_on_target_against',
    'shots_on_target_against_per90',
    'wins',
    'draws',
    'losses',
    'penalties_saved',
    'penalty_goals_conceded',
  ],
};

const POSITION_BADGE_CLASSES: Record<PositionGroup, string> = {
  forward: 'bg-forward',
  midfielder: 'bg-midfielder',
  defender: 'bg-defender',
  goalkeeper: 'bg-goalkeeper',
};

const SPECIAL_STAT_LABELS: Record<string, string> = {
  goals_assists: 'Goals + Assists',
  goals_assists_per90: 'G+A / 90',
  goals_per90: 'Goals / 90',
  assists_per90: 'Assists / 90',
  shots_per90: 'Shots / 90',
  shots_on_target: 'Shots on Target',
  shots_on_target_per90: 'SoT / 90',
  crosses_per90: 'Crosses / 90',
  fouls_drawn_per90: 'Fouls Drawn / 90',
  fouls_committed_per90: 'Fouls / 90',
  tackles_won: 'Tackles Won',
  tackles_won_per90: 'Tackles Won / 90',
  interceptions_per90: 'Interceptions / 90',
  save_pct: 'Save Pct',
  clean_sheet_pct: 'Clean Sheet Pct',
  goals_against: 'Goals Against',
  goals_against_per90: 'GA / 90',
  saves_per90: 'Saves / 90',
  shots_on_target_against: 'Shots Faced',
  shots_on_target_against_per90: 'Shots Faced / 90',
  team_goals_on_pitch_per90: 'Team GF / 90',
  team_goals_against_on_pitch_per90: 'Team GA / 90',
  team_goals_against_on_pitch: 'Team GA on Pitch',
};

function formatStatLabel(snakeKey: string): string {
  if (SPECIAL_STAT_LABELS[snakeKey]) {
    return SPECIAL_STAT_LABELS[snakeKey];
  }
  return snakeKey
    .replace(/_per90$/i, ' / 90')
    .replace(/_pct$/i, ' %')
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function formatStatValue(val: number | null | undefined, key: string): string {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const isPercent = key.endsWith('_pct') || key === 'save_pct';
  const isPer90 = key.endsWith('_per90');
  const isDecimal = !Number.isInteger(val) || isPer90 || isPercent;

  if (isPercent) return `${val.toFixed(1)}%`;
  if (isDecimal) return val.toFixed(2);
  return Math.round(val).toLocaleString();
}

export const PlayerDetailDrawer: React.FC<PlayerDetailDrawerProps> = ({
  player,
  allPlayers,
  onClose,
  onSelectPlayer,
}) => {
  const [showAllSimilar, setShowAllSimilar] = useState(false);

  // Reset showAllSimilar when player changes
  useEffect(() => {
    setShowAllSimilar(false);
  }, [player?.name]);

  // Lock body scroll and handle Escape key
  useEffect(() => {
    if (!player) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [player, onClose]);

  if (!player) return null;

  const group = player.position_group || 'forward';
  const groupLabel = group.charAt(0).toUpperCase() + group.slice(1);
  const badgeClass = POSITION_BADGE_CLASSES[group] || POSITION_BADGE_CLASSES.forward;

  const statKeys = DETAIL_STATS_KEYS[group] || Object.keys(player.stats || {}).slice(0, 15);
  const similarList = Array.isArray(player.similar) ? player.similar : [];
  const displayedSimilar = showAllSimilar
    ? similarList.slice(0, 20)
    : similarList.slice(0, 5);

  const handleSimilarClick = (simName: string, simClub: string) => {
    const target =
      allPlayers.find((p) => p.name === simName && p.club === simClub) ||
      allPlayers.find((p) => p.name === simName);

    if (target) {
      onSelectPlayer(target);
    } else {
      console.warn(`Profile for ${simName} not found in master list.`);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Scouting profile for ${player.name}`}
      className="fixed inset-0 z-50 overflow-hidden"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Container */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-6 sm:pl-10">
        <div className="w-screen max-w-[580px] bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
          {/* Header */}
          <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-4 bg-slate-50/50 dark:bg-slate-800/50">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 flex-wrap">
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight leading-snug">
                  {player.name}
                </h2>
                <span
                  className={`px-2.5 py-0.5 rounded-lg text-[11px] font-extrabold uppercase tracking-wider text-white shadow-xs ${badgeClass}`}
                >
                  {groupLabel}
                </span>
              </div>

              <div className="flex items-center gap-2 mt-1.5 text-xs sm:text-sm text-slate-500 dark:text-slate-400 flex-wrap">
                <span className="font-semibold text-slate-900 dark:text-slate-200">
                  {player.club || 'Premier League'}
                </span>
                <span aria-hidden="true">•</span>
                <span>{player.position}</span>
                <span aria-hidden="true">•</span>
                <span>{player.age ? `Age ${player.age}` : 'Age —'}</span>
                <span aria-hidden="true">•</span>
                <span className="mono-num font-semibold text-pitch">
                  {player.minutes ? `${player.minutes.toLocaleString()} mins` : '0 mins'}
                  {player.nineties ? ` (${player.nineties.toFixed(1)} 90s)` : ''}
                </span>
              </div>
            </div>

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              aria-label="Close scouting profile drawer"
              className="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-300 flex items-center justify-center font-bold text-base cursor-pointer transition-colors shrink-0"
            >
              ✕
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-5 sm:p-6 flex flex-col gap-6 scrollbar-thin">
            {/* Low Sample Warning Banner */}
            {player.low_sample && (
              <div className="flex items-start gap-3 p-3.5 rounded-xl bg-amber/15 border border-amber/35 text-amber-900 dark:text-amber dark:bg-amber/20 text-xs">
                <span className="text-amber text-sm mt-0.5">⚠️</span>
                <div>
                  <strong className="font-semibold">Low Sample Warning:</strong> This player has played fewer than 90 league minutes ({player.minutes ?? 0}m). Per-90 ratios and style projections may exhibit high volatility.
                </div>
              </div>
            )}

            {/* Detailed Statistical Profile Grid */}
            <section>
              <div className="flex items-baseline justify-between mb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Detailed Statistical Profile
                </h3>
                <span className="text-[11px] text-slate-400 dark:text-slate-500">
                  Normalized & per-90 metrics
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {statKeys.map((key) => {
                  const val = player.stats ? player.stats[key] : null;
                  if (val === undefined || val === null) return null;
                  const displayVal = formatStatValue(val, key);

                  return (
                    <div
                      key={key}
                      className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
                    >
                      <span className="mono-num text-lg font-bold text-slate-900 dark:text-slate-100">
                        {displayVal}
                      </span>
                      <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-tight mt-1 line-clamp-1">
                        {formatStatLabel(key)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Closest Statistical Style Matches */}
            <section className="flex flex-col gap-3 pt-4 border-t border-slate-200/80 dark:border-slate-800">
              <div className="flex items-baseline justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Closest Style Matches
                </h3>
                <span className="text-[11px] text-slate-400 dark:text-slate-500">
                  Cosine Similarity
                </span>
              </div>

              {/* Statistical note */}
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                {group === 'midfielder' ? (
                  <>
                    <strong className="text-slate-700 dark:text-slate-300">Midfielder Constraint:</strong> Cosine similarity is computed using defensive actions, shooting, and disciplinary records. Passing progression and creation metrics were not published in the source release.
                  </>
                ) : (
                  <>
                    Matches represent statistical output profiles within the {groupLabel.toLowerCase()} pool, not proof of identical tactical roles or talent level.
                  </>
                )}
              </div>

              {/* Similar Players List */}
              {similarList.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400 dark:text-slate-500">
                  No precomputed statistical matches available for this profile.
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {displayedSimilar.map((sim) => {
                    const pct = Math.max(0, Math.min(100, Math.round(sim.similarity * 100)));

                    return (
                      <button
                        key={`${sim.player}-${sim.club}`}
                        type="button"
                        onClick={() => handleSimilarClick(sim.player, sim.club)}
                        className="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-800 hover:border-pitch hover:bg-slate-50 dark:hover:bg-slate-800 hover:translate-x-1 transition-all duration-150 text-left cursor-pointer group"
                      >
                        <div className="flex-1 min-w-0 pr-3">
                          <div className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-pitch transition-colors truncate">
                            {sim.player}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            {sim.club || 'Premier League'}
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          {/* Meter bar */}
                          <div className="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden hidden sm:block">
                            <div
                              className="h-full bg-pitch rounded-full transition-all duration-300"
                              style={{ width: `${pct}%` }}
                            />
                          </div>

                          {/* Score Badge */}
                          <span className="mono-num text-xs font-bold px-2 py-0.5 rounded-md bg-pitch/10 text-pitch border border-pitch/20">
                            {pct}% match
                          </span>
                        </div>
                      </button>
                    );
                  })}

                  {/* Toggle Show More / Top 5 */}
                  {similarList.length > 5 && (
                    <button
                      type="button"
                      onClick={() => setShowAllSimilar(!showAllSimilar)}
                      className="mt-2 py-2 px-4 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 self-center transition-colors cursor-pointer"
                    >
                      {showAllSimilar
                        ? 'Show Top 5 Only'
                        : `Show More (${Math.min(20, similarList.length) - 5} more)`}
                    </button>
                  )}
                </div>
              )}
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};
