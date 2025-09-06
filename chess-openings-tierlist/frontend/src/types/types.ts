// Type definitions for chess openings tier list

export interface Opening {
  id: number;
  eco_code?: string;
  name?: string;
  moves_sequence: string[];
  moves_string: string;
  popularity_rank?: number;
}

export interface OpeningStatistic {
  id: number;
  opening_id: number;
  white_wins: number;
  black_wins: number;
  draws: number;
  total_games: number;
  win_rate_white: number;
  win_rate_black: number;
  draw_rate: number;
  performance_score: number;
  rating_range?: string;
  time_control?: string;
  average_rating?: number;
  collected_at: string;
}

export interface TierListItem {
  opening: Opening;
  statistics: OpeningStatistic;
  tier_rank?: string;
  tier_position?: number;
}

export interface FilterParams {
  rating_range?: string;
  time_control?: string;
  min_games?: number;
  sort_by?: string;
  order?: 'asc' | 'desc';
  limit?: number;
}

export interface StatisticsSummary {
  total_openings: number;
  total_statistics: number;
  last_updated?: string;
  available_rating_ranges: string[];
  available_time_controls: string[];
}

export const TIER_RANKS = ['S', 'A', 'B', 'C', 'D'] as const;
export type TierRank = typeof TIER_RANKS[number];

export const TIER_COLORS = {
  S: '#ff7f00', // Orange
  A: '#ff0000', // Red
  B: '#ffff00', // Yellow
  C: '#00ff00', // Green
  D: '#0080ff', // Blue
} as const;