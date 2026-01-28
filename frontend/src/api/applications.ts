/**
 * API functions for application endpoints.
 */

import apiClient from './client';
import type {
  LoanApplicationInput,
  ApplicationResponse,
  ApplicationStatus,
} from '../types/application';

const API_PREFIX = '/api/v1';

/**
 * Submit a new loan application.
 */
export async function submitApplication(
  input: LoanApplicationInput
): Promise<ApplicationResponse> {
  const response = await apiClient.post<ApplicationResponse>(
    `${API_PREFIX}/applications/`,
    input
  );
  return response.data;
}

/**
 * Get application status by ID.
 */
export async function getApplicationStatus(
  applicationId: string
): Promise<ApplicationStatus> {
  const response = await apiClient.get<ApplicationStatus>(
    `${API_PREFIX}/applications/${applicationId}/status`
  );
  return response.data;
}

/**
 * Poll for application completion.
 * Returns when the application is no longer processing, or on timeout.
 */
export async function waitForApplicationCompletion(
  applicationId: string,
  options: {
    pollInterval?: number;
    maxAttempts?: number;
  } = {}
): Promise<ApplicationStatus> {
  const { pollInterval = 2000, maxAttempts = 30 } = options;
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await getApplicationStatus(applicationId);

    if (status.status !== 'processing' && status.status !== 'pending') {
      return status;
    }

    attempts++;
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  throw new Error('Application processing timed out');
}
