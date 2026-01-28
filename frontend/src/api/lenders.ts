/**
 * API functions for lender endpoints.
 */

import apiClient from './client';
import type {
  LenderSummary,
  LenderDetail,
  LenderCreate,
  LenderUpdate,
  ProgramDetail,
} from '../types/lender';

const API_PREFIX = '/api/v1';

/**
 * List all lenders.
 */
export async function listLenders(): Promise<LenderSummary[]> {
  const response = await apiClient.get<LenderSummary[]>(
    `${API_PREFIX}/lenders/`
  );
  return response.data;
}

/**
 * Get a specific lender by ID.
 */
export async function getLender(lenderId: string): Promise<LenderDetail> {
  const response = await apiClient.get<LenderDetail>(
    `${API_PREFIX}/lenders/${lenderId}`
  );
  return response.data;
}

/**
 * Create a new lender.
 */
export async function createLender(input: LenderCreate): Promise<LenderDetail> {
  const response = await apiClient.post<LenderDetail>(
    `${API_PREFIX}/lenders/`,
    input
  );
  return response.data;
}

/**
 * Update an existing lender.
 */
export async function updateLender(
  lenderId: string,
  input: LenderUpdate
): Promise<LenderDetail> {
  const response = await apiClient.put<LenderDetail>(
    `${API_PREFIX}/lenders/${lenderId}`,
    input
  );
  return response.data;
}

/**
 * Toggle lender active status.
 */
export async function toggleLenderStatus(
  lenderId: string
): Promise<{ id: string; name: string; is_active: boolean; message: string }> {
  const response = await apiClient.patch<{
    id: string;
    name: string;
    is_active: boolean;
    message: string;
  }>(`${API_PREFIX}/lenders/${lenderId}/status`);
  return response.data;
}

/**
 * Delete a lender.
 */
export async function deleteLender(lenderId: string): Promise<void> {
  await apiClient.delete(`${API_PREFIX}/lenders/${lenderId}`);
}

/**
 * List programs for a lender.
 */
export async function listLenderPrograms(
  lenderId: string
): Promise<ProgramDetail[]> {
  const response = await apiClient.get<ProgramDetail[]>(
    `${API_PREFIX}/lenders/${lenderId}/programs`
  );
  return response.data;
}
