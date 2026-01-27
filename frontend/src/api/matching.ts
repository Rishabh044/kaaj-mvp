/**
 * API functions for matching results.
 */

import apiClient from './client';
import type { MatchingResults } from '../types/matching';

const API_PREFIX = '/api/v1';

/**
 * Get matching results for an application.
 */
export async function getMatchingResults(
  applicationId: string
): Promise<MatchingResults> {
  const response = await apiClient.get<MatchingResults>(
    `${API_PREFIX}/applications/${applicationId}/results`
  );
  return response.data;
}
