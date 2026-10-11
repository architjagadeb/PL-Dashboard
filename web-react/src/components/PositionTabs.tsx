import React from 'react';
import type { PositionGroup } from '../types';

export type PositionTabValue = 'all' | PositionGroup;

interface PositionTabsProps {
  value: PositionTabValue;
  onChange: (value: PositionTabValue) => void;
  counts?: Record<PositionTabValue, number>;
}

interface TabConfig {
  key: PositionTabValue;
  label: string;
  dotColor: string;
  activeBg: string;
}

const TABS: TabConfig[] = [
  {
    key: 'all',
    label: 'All Players',
    dotColor: 'bg-pitch',
    activeBg: 'bg-pitch',
  },
  {
    key: 'forward',
    label: 'Forwards',
    dotColor: 'bg-forward',
    activeBg: 'bg-forward',
  },
  {
    key: 'midfielder',
    label: 'Midfielders',
    dotColor: 'bg-midfielder',
    activeBg: 'bg-midfielder',
  },
  {
    key: 'defender',
    label: 'Defenders',
    dotColor: 'bg-defender',
    activeBg: 'bg-defender',
  },
  {
    key: 'goalkeeper',
    label: 'Goalkeepers',
    dotColor: 'bg-goalkeeper',
    activeBg: 'bg-goalkeeper',
  },
];

export const PositionTabs: React.FC<PositionTabsProps> = ({
  value,
  onChange,
  counts,
}) => {
  return (
    <div
      role="tablist"
      aria-label="Filter players by position"
      className="inline-flex p-1 bg-slate-100 dark:bg-[#16202c] border border-slate-200 dark:border-[#233142] rounded-xl overflow-x-auto max-w-full scrollbar-none"
    >
      {TABS.map((tab) => {
        const isActive = value === tab.key;
        return (
          <button
            key={tab.key}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.key)}
            className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs md:text-sm font-semibold transition-all duration-150 whitespace-nowrap cursor-pointer select-none ${
              isActive
                ? `${tab.activeBg} text-white shadow-sm`
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-700/40'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isActive ? 'bg-white ring-1 ring-white/50' : tab.dotColor
              }`}
              aria-hidden="true"
            />
            <span>{tab.label}</span>
            {counts && counts[tab.key] !== undefined && (
              <span
                className={`text-[11px] px-1.5 py-0.5 rounded-full mono-num font-medium ${
                  isActive
                    ? 'bg-white/20 text-white'
                    : 'bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                }`}
              >
                {counts[tab.key]}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
