export type PositionGroup = 'forward' | 'midfielder' | 'defender' | 'goalkeeper';

export interface SimilarMatch {
  player: string;
  club: string;
  similarity: number;
}

export interface Player {
  name: string;
  club: string;
  position: string;
  position_group: PositionGroup;
  age: number;
  minutes: number;
  nineties: number;
  low_sample: boolean;
  pca: {
    x: number;
    y: number;
  };
  stats: Record<string, number | null>;
  similar: SimilarMatch[];
}

export interface Meta {
  season: string;
  source: string;
  generated_at: string;
  position_groups: string[] | Record<string, any>;
}

export interface PlayersData {
  meta: Meta;
  players: Player[];
}
