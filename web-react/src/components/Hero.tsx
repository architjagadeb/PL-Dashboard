import React from 'react';
import { useCountUp } from '../hooks/useCountUp';

interface HeroProps {
  playerCount: number;
  clubCount: number;
  season?: string;
  loading: boolean;
  onStartScouting?: () => void;
}

export const Hero: React.FC<HeroProps> = ({
  playerCount,
  clubCount,
  season = '2025–26',
  loading,
  onStartScouting,
}) => {
  const animatedPlayerCount = useCountUp(playerCount, {
    duration: 800,
    decimals: 0,
    enabled: !loading && playerCount > 0,
  });

  const handleScrollToScouting = () => {
    if (onStartScouting) {
      onStartScouting();
      return;
    }
    const filterBar = document.getElementById('scouting-controls');
    if (filterBar) {
      filterBar.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section
      aria-label="Premier League scouting introduction"
      className="relative w-full overflow-hidden rounded-3xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900/90 my-4 sm:my-6 md:h-[80vh] md:min-h-[580px] md:max-h-[760px] flex flex-col justify-center items-center text-center px-4 sm:px-8 py-12 sm:py-16 md:py-0 shadow-xs"
    >
      {/* Animated diagonal pitch stripes pattern (CSS only, pitch opacity < 8%) */}
      <div
        className="absolute inset-0 pointer-events-none hero-diagonal-stripes opacity-90"
        aria-hidden="true"
      />

      {/* Hero content container */}
      <div className="relative z-10 max-w-4xl mx-auto flex flex-col items-center gap-5 sm:gap-6">
        {/* Eyebrow Label */}
        <div className="font-mono text-xs sm:text-sm uppercase tracking-[0.2em] font-bold text-pitch bg-pitch/10 px-3.5 py-1 rounded-full border border-pitch/20">
          2025-26 Premier League
        </div>

        {/* Main Headline */}
        <h1 className="font-sans font-extrabold tracking-tight text-slate-900 dark:text-slate-50 text-4xl sm:text-5xl md:text-6xl lg:text-7xl leading-[1.08] max-w-3xl">
          Find Your Player’s{' '}
          <span className="text-pitch underline decoration-pitch/30 decoration-wavy decoration-2 underline-offset-8">
            Statistical Twin
          </span>
        </h1>

        {/* Subtext */}
        <p className="font-sans text-sm sm:text-base md:text-lg text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
          Style-based scouting across per-90 metrics, PCA tactical positioning, and cosine similarity profiles for every Premier League player.
        </p>

        {/* Stat Row */}
        <div className="w-full max-w-xl my-2 pt-2">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 w-full">
            {/* Stat 1: Players Tracked */}
            <div className="p-3.5 sm:p-4 rounded-2xl bg-slate-50/80 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 flex flex-col items-center justify-center">
              <span className="font-mono font-bold text-2xl sm:text-3xl text-pitch leading-tight">
                {loading ? '—' : animatedPlayerCount}
              </span>
              <span className="font-sans text-[11px] sm:text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">
                Players Tracked
              </span>
            </div>

            {/* Stat 2: Clubs Covered */}
            <div className="p-3.5 sm:p-4 rounded-2xl bg-slate-50/80 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 flex flex-col items-center justify-center">
              <span className="font-mono font-bold text-2xl sm:text-3xl text-slate-900 dark:text-slate-100 leading-tight">
                {loading ? '—' : clubCount || 20}
              </span>
              <span className="font-sans text-[11px] sm:text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">
                Clubs Covered
              </span>
            </div>

            {/* Stat 3: Season */}
            <div className="col-span-2 sm:col-span-1 p-3.5 sm:p-4 rounded-2xl bg-slate-50/80 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 flex flex-col items-center justify-center">
              <span className="font-mono font-bold text-2xl sm:text-3xl text-slate-900 dark:text-slate-100 leading-tight">
                {loading ? '—' : season}
              </span>
              <span className="font-sans text-[11px] sm:text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">
                Season
              </span>
            </div>
          </div>
        </div>

        {/* CTA Button */}
        <div className="mt-2">
          <button
            type="button"
            onClick={handleScrollToScouting}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-pitch hover:bg-emerald-700 active:scale-95 text-white font-sans font-bold text-sm sm:text-base shadow-sm hover:shadow-md transition-all duration-150 cursor-pointer"
          >
            <span>Start scouting</span>
            <span aria-hidden="true" className="text-base animate-bounce">
              ↓
            </span>
          </button>
        </div>
      </div>
    </section>
  );
};
