import React, { useEffect, useState } from 'react';
import type { Player } from '../types';
import { PlayerCard } from './PlayerCard';

interface PlayerGridProps {
  players: Player[];
  filterKey?: string;
  onPlayerClick?: (player: Player) => void;
}

export const PlayerGrid: React.FC<PlayerGridProps> = ({
  players,
  filterKey = '',
  onPlayerClick,
}) => {
  // Sort players by minutes descending
  const sortedPlayers = [...players].sort((a, b) => (b.minutes ?? 0) - (a.minutes ?? 0));

  // Cross-fade animation effect on filter changes
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    setIsTransitioning(true);
    const timer = setTimeout(() => {
      setIsTransitioning(false);
    }, 150);

    return () => clearTimeout(timer);
  }, [filterKey, players.length]);

  return (
    <div
      className={`transition-opacity duration-150 ease-in-out ${
        isTransitioning ? 'opacity-40' : 'opacity-100'
      }`}
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-5">
        {sortedPlayers.map((player, index) => (
          <PlayerCard
            key={`${player.name}-${player.club}-${player.position}`}
            player={player}
            index={index}
            onClick={onPlayerClick}
          />
        ))}
      </div>
    </div>
  );
};
