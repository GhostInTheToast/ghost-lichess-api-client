// API service for interacting with the backend

import axios from 'axios';
import { Opening, OpeningStatistic, TierListItem, FilterParams, StatisticsSummary } from '../types/types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export class ApiService {
  // Get list of openings with filtering
  static async getOpenings(filters?: FilterParams): Promise<Opening[]> {
    const params = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await api.get(`/openings?${params.toString()}`);
    return response.data;
  }

  // Get a specific opening by ID
  static async getOpening(id: number): Promise<Opening> {
    const response = await api.get(`/openings/${id}`);
    return response.data;
  }

  // Get statistics for a specific opening
  static async getOpeningStatistics(
    openingId: number,
    ratingRange?: string,
    timeControl?: string
  ): Promise<OpeningStatistic[]> {
    const params = new URLSearchParams();
    if (ratingRange) params.append('rating_range', ratingRange);
    if (timeControl) params.append('time_control', timeControl);
    
    const response = await api.get(`/openings/${openingId}/statistics?${params.toString()}`);
    return response.data;
  }

  // Get tier list data
  static async getTierList(
    ratingRange: string = 'all',
    timeControl: string = 'all',
    userId: string = 'default'
  ): Promise<TierListItem[]> {
    const params = new URLSearchParams({
      rating_range: ratingRange,
      time_control: timeControl,
      user_id: userId,
    });
    
    const response = await api.get(`/tier-list?${params.toString()}`);
    return response.data;
  }

  // Update tier list
  static async updateTierList(
    updates: Array<{
      opening_id: number;
      tier_rank: string;
      tier_position: number;
    }>,
    ratingRange: string = 'all',
    timeControl: string = 'all',
    userId: string = 'default'
  ): Promise<void> {
    const params = new URLSearchParams({
      rating_range: ratingRange,
      time_control: timeControl,
      user_id: userId,
    });
    
    await api.post(`/tier-list?${params.toString()}`, updates);
  }

  // Get statistics summary
  static async getStatisticsSummary(): Promise<StatisticsSummary> {
    const response = await api.get('/statistics/summary');
    return response.data;
  }

  // Get top performers
  static async getTopPerformers(
    limit: number = 10,
    metric: string = 'performance_score'
  ): Promise<Array<{
    opening: Opening;
    statistics: OpeningStatistic;
    metric_value: number;
  }>> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      metric,
    });
    
    const response = await api.get(`/statistics/top-performers?${params.toString()}`);
    return response.data;
  }
}

// Error handling wrapper
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};