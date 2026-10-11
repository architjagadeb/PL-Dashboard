import React from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Search player (e.g. Saka, Saliba, Raya)...',
}) => {
  return (
    <div className="relative flex items-center w-full">
      <label htmlFor="player-search-input" className="sr-only">
        Search player by name
      </label>
      <span
        className="absolute left-3.5 pointer-events-none text-slate-400 dark:text-slate-500 flex items-center"
        aria-hidden="true"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </span>
      <input
        type="text"
        id="player-search-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck="false"
        className="w-full h-[42px] pl-10 pr-9 bg-white dark:bg-[#131c26] border border-slate-200 dark:border-[#233142] rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 shadow-xs focus:outline-none focus:border-pitch focus:ring-2 focus:ring-pitch/30 transition-all duration-150"
      />
      {value.trim().length > 0 && (
        <button
          type="button"
          onClick={() => onChange('')}
          aria-label="Clear search query"
          className="absolute right-2.5 w-5 h-5 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-500 dark:text-slate-300 text-xs font-bold cursor-pointer transition-colors"
        >
          ✕
        </button>
      )}
    </div>
  );
};
