import React from 'react';

interface ClubFilterProps {
  clubs: string[];
  selectedClub: string;
  onChange: (club: string) => void;
}

export const ClubFilter: React.FC<ClubFilterProps> = ({
  clubs,
  selectedClub,
  onChange,
}) => {
  return (
    <div className="relative flex items-center w-full">
      <label htmlFor="club-filter-select" className="sr-only">
        Filter by Club
      </label>
      <select
        id="club-filter-select"
        value={selectedClub}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-[42px] pl-3.5 pr-9 bg-white dark:bg-[#131c26] border border-slate-200 dark:border-[#233142] rounded-lg text-sm font-medium text-slate-800 dark:text-slate-100 shadow-xs appearance-none cursor-pointer focus:outline-none focus:border-pitch focus:ring-2 focus:ring-pitch/30 transition-all duration-150"
      >
        <option value="all">All Clubs ({clubs.length > 0 ? `${clubs.length} clubs` : 'Loading...'})</option>
        {clubs.map((club) => (
          <option key={club} value={club}>
            {club}
          </option>
        ))}
      </select>
      <span
        className="absolute right-3 pointer-events-none text-slate-400 dark:text-slate-500 flex items-center"
        aria-hidden="true"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </span>
    </div>
  );
};
