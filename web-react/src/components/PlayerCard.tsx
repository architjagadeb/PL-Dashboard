import React from 'react';
import type { Player, PositionGroup } from '../types';

interface PlayerCardProps {
  player: Player;
  index: number;
  onClick?: (player: Player) => void;
}

interface StatSpec {
  key: string;
  label: string;
  format: 'int' | 'decimal' | 'percent';
}

const STATS_BY_GROUP: Record<PositionGroup, StatSpec[]> = {
  forward: [
    { key: 'goals', label: 'Goals', format: 'int' },
    { key: 'assists', label: 'Assists', format: 'int' },
    { key: 'goals_per90', label: 'G / 90', format: 'decimal' },
  ],
  midfielder: [
    { key: 'goals_assists', label: 'G + A', format: 'int' },
    { key: 'tackles_won_per90', label: 'TklW / 90', format: 'decimal' },
    { key: 'interceptions_per90', label: 'Int / 90', format: 'decimal' },
  ],
  defender: [
    { key: 'tackles_won_per90', label: 'TklW / 90', format: 'decimal' },
    { key: 'interceptions_per90', label: 'Int / 90', format: 'decimal' },
    { key: 'fouls_committed_per90', label: 'Fouls / 90', format: 'decimal' },
  ],
  goalkeeper: [
    { key: 'saves', label: 'Saves', format: 'int' },
    { key: 'save_pct', label: 'Save %', format: 'percent' },
    { key: 'clean_sheets', label: 'Clean Sheets', format: 'int' },
  ],
};

const POSITION_META: Record<
  PositionGroup,
  {
    label: string;
    borderClass: string;
    chipBg: string;
    accentText: string;
    glowClass: string;
  }
> = {
  forward: {
    label: 'Forward',
    borderClass: 'border-l-forward',
    chipBg: 'bg-forward',
    accentText: 'text-forward',
    glowClass: 'card-glow-forward',
  },
  midfielder: {
    label: 'Midfielder',
    borderClass: 'border-l-midfielder',
    chipBg: 'bg-midfielder',
    accentText: 'text-midfielder',
    glowClass: 'card-glow-midfielder',
  },
  defender: {
    label: 'Defender',
    borderClass: 'border-l-defender',
    chipBg: 'bg-defender',
    accentText: 'text-defender',
    glowClass: 'card-glow-defender',
  },
  goalkeeper: {
    label: 'Goalkeeper',
    borderClass: 'border-l-goalkeeper',
    chipBg: 'bg-goalkeeper',
    accentText: 'text-goalkeeper',
    glowClass: 'card-glow-goalkeeper',
  },
};

function formatStatValue(value: number | null | undefined, format: 'int' | 'decimal' | 'percent'): string {
  if (value === null || value === undefined) return '—';
  if (format === 'percent') return `${value.toFixed(1)}%`;
  if (format === 'int') return Math.round(value).toLocaleString();
  return value.toFixed(2);
}

export const PlayerCard: React.FC<PlayerCardProps> = ({
  player,
  index,
  onClick,
}) => {
  const group = player.position_group || 'forward';
  const meta = POSITION_META[group] || POSITION_META.forward;
  const statSpecs = STATS_BY_GROUP[group] || STATS_BY_GROUP.forward;

  const handleClick = () => {
    if (onClick) {
      onClick(player);
    } else {
      console.log('Player clicked:', player.name);
    }
  };

  const staggerIndex = Math.min(index, 24);

  return (
    <button
      type="button"
      onClick={handleClick}
      style={{ '--stagger-index': staggerIndex } as React.CSSProperties}
      className={`card-stagger-rise group relative text-left w-full flex flex-col justify-between p-4 md:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 border-l-4 ${meta.borderClass} ${meta.glowClass} shadow-xs hover:-translate-y-1 hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-200 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-pitch`}
    >
      <div>
        {/* Top Header: Identity & Position Chip */}
        <div className="flex items-start justify-between gap-3 mb-2.5">
          <div className="flex-1 min-w-0">
            {/* Player name allowed to wrap to 2 lines, never truncated with ellipsis */}
            <h3 className="text-base md:text-[17px] font-bold text-slate-900 dark:text-slate-100 leading-snug line-clamp-2 break-words">
              {player.name}
            </h3>
            {/* Club and specific position */}
            <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-500 dark:text-slate-400">
              <span className="font-semibold text-slate-700 dark:text-slate-300 truncate">
                {player.club}
              </span>
              <span aria-hidden="true">•</span>
              <span className="shrink-0">{player.position}</span>
            </div>
          </div>

          {/* Solid-background position chip with white text */}
          <span
            className={`shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-extrabold uppercase tracking-wider text-white shadow-xs ${meta.chipBg}`}
          >
            {meta.label}
          </span>
        </div>

        {/* Low-sample badge (amber-toned) */}
        {player.low_sample && (
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 mb-3 rounded-md text-[11px] font-semibold bg-amber/15 border border-amber/35 text-amber-900 dark:text-amber dark:bg-amber/20">
            <span className="text-amber text-[8px]" aria-hidden="true">
              ●
            </span>
            <span>Low sample ({player.minutes}m / &lt;90m)</span>
          </div>
        )}
      </div>

      {/* Stats Section & Footer */}
      <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
        <div className="grid grid-cols-3 gap-2 text-center items-end">
          {statSpecs.map((spec, statIdx) => {
            const rawVal = player.stats ? player.stats[spec.key] : null;
            const displayVal = formatStatValue(rawVal, spec.format);
            const isFirst = statIdx === 0;

            return (
              <div
                key={spec.key}
                className="flex flex-col items-center justify-end"
              >
                <span
                  className={`mono-num tracking-tight ${
                    isFirst
                      ? `text-xl md:text-[22px] font-extrabold leading-tight ${meta.accentText}`
                      : 'text-sm md:text-[15px] font-semibold text-slate-600 dark:text-slate-400 leading-snug'
                  }`}
                >
                  {displayVal}
                </span>
                <span
                  className={`mt-1 uppercase text-[10px] md:text-[11px] truncate max-w-full ${
                    isFirst
                      ? 'font-bold text-slate-700 dark:text-slate-300'
                      : 'font-medium text-slate-400 dark:text-slate-500'
                  }`}
                >
                  {spec.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Card CTA Footer */}
        <div className="flex items-center justify-between mt-3 pt-2 text-[11px] font-semibold text-slate-400 dark:text-slate-500 border-t border-dashed border-slate-100 dark:border-slate-800/60">
          <span className="mono-num text-slate-500 dark:text-slate-400">
            {player.minutes.toLocaleString()} mins
          </span>
          <span className="text-pitch font-medium group-hover:underline">
            Scouting Profile →
          </span>
        </div>
      </div>
    </button>
  );
};
