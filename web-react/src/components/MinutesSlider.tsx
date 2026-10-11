import React from 'react';

interface MinutesSliderProps {
  value: number;
  max: number;
  onChange: (value: number) => void;
  step?: number;
}

export const MinutesSlider: React.FC<MinutesSliderProps> = ({
  value,
  max,
  onChange,
  step = 90,
}) => {
  const safeMax = Math.max(max, 90);
  const percentage = Math.min(100, Math.max(0, (value / safeMax) * 100));

  return (
    <div className="flex flex-col gap-1 w-full">
      <div className="flex items-center justify-between text-xs font-semibold">
        <label
          htmlFor="minutes-slider-input"
          className="text-slate-600 dark:text-slate-300"
        >
          Minutes Played
        </label>
        <span className="mono-num px-2 py-0.5 rounded-md bg-slate-100 dark:bg-[#1c2836] border border-slate-200 dark:border-slate-700/60 text-slate-800 dark:text-emerald-400 font-bold text-[11px]">
          ≥ {value.toLocaleString()} mins
        </span>
      </div>
      <div className="relative flex items-center h-6">
        <input
          type="range"
          id="minutes-slider-input"
          min={0}
          max={safeMax}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          aria-valuemin={0}
          aria-valuemax={safeMax}
          aria-valuenow={value}
          className="w-full h-2 bg-slate-200 dark:bg-[#1d2938] rounded-lg appearance-none cursor-pointer accent-pitch focus:outline-none focus:ring-2 focus:ring-pitch/30 transition-all"
          style={{
            background: `linear-gradient(to right, #1f8a4c ${percentage}%, #e2e8f0 ${percentage}%)`,
          }}
        />
      </div>
    </div>
  );
};
