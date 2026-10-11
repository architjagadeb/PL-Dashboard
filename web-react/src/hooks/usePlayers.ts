import { useEffect, useState } from 'react';
import type { Meta, Player, PlayersData } from '../types';

export interface UsePlayersResult {
  players: Player[];
  meta: Meta | null;
  loading: boolean;
  error: string | null;
}

export function usePlayers(): UsePlayersResult {
  const [players, setPlayers] = useState<Player[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchPlayers() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/data/players.json', {
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to load player data: ${response.status} ${response.statusText}`);
        }

        const data: PlayersData = await response.json();

        if (!data || !Array.isArray(data.players)) {
          throw new Error('Invalid data format received from players.json');
        }

        setPlayers(data.players);
        setMeta(data.meta ?? null);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          return;
        }
        const message = err instanceof Error ? err.message : 'An unknown error occurred while fetching data';
        setError(message);
      } finally {
        setLoading(false);
      }
    }

    fetchPlayers();

    return () => {
      controller.abort();
    };
  }, []);

  return { players, meta, loading, error };
}
