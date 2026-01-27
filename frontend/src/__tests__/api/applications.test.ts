/**
 * Tests for the applications API functions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  submitApplication,
  getApplicationStatus,
  waitForApplicationCompletion,
} from '../../api/applications';
import apiClient from '../../api/client';
import type { LoanApplicationInput } from '../../types';

// Mock the API client
vi.mock('../../api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('applications API', () => {
  const mockInput: LoanApplicationInput = {
    applicant: {
      fico_score: 720,
      is_homeowner: true,
      is_us_citizen: true,
      has_cdl: false,
    },
    business: {
      name: 'Test Business',
      state: 'TX',
      years_in_business: 5,
    },
    credit_history: {
      has_bankruptcy: false,
      has_open_judgements: false,
      has_foreclosure: false,
      has_repossession: false,
      has_tax_liens: false,
    },
    equipment: {
      category: 'construction',
      year: 2022,
      condition: 'used',
    },
    loan_request: {
      amount: 5000000,
      transaction_type: 'purchase',
      is_private_party: false,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('submitApplication', () => {
    it('submitApplication_success', async () => {
      const mockResponse = {
        data: {
          id: 'test-123',
          application_number: 'APP-20260128-ABC123',
          status: 'processing',
          workflow_run_id: 'run-456',
          message: 'Application submitted successfully',
        },
      };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await submitApplication(mockInput);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/applications/',
        mockInput
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('submitApplication_validation_error', async () => {
      const mockError = {
        message: 'Validation Error',
        status: 422,
        details: { detail: 'Invalid input' },
      };
      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      await expect(submitApplication(mockInput)).rejects.toEqual(mockError);
    });
  });

  describe('getApplicationStatus', () => {
    it('getApplicationStatus_success', async () => {
      const mockResponse = {
        data: {
          application_id: 'test-123',
          status: 'completed',
          total_evaluated: 5,
          total_eligible: 3,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getApplicationStatus('test-123');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/applications/test-123/status'
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('getApplicationStatus_not_found', async () => {
      const mockError = {
        message: 'Application not found',
        status: 404,
      };
      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(getApplicationStatus('invalid-id')).rejects.toEqual(
        mockError
      );
    });
  });

  describe('waitForApplicationCompletion', () => {
    it('returns_immediately_when_completed', async () => {
      const mockResponse = {
        data: {
          application_id: 'test-123',
          status: 'completed',
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await waitForApplicationCompletion('test-123');

      expect(result.status).toBe('completed');
      expect(apiClient.get).toHaveBeenCalledTimes(1);
    });

    it('polls_until_completed', async () => {
      vi.mocked(apiClient.get)
        .mockResolvedValueOnce({
          data: { application_id: 'test-123', status: 'processing' },
        })
        .mockResolvedValueOnce({
          data: { application_id: 'test-123', status: 'processing' },
        })
        .mockResolvedValueOnce({
          data: { application_id: 'test-123', status: 'completed' },
        });

      const result = await waitForApplicationCompletion('test-123', {
        pollInterval: 10,
      });

      expect(result.status).toBe('completed');
      expect(apiClient.get).toHaveBeenCalledTimes(3);
    });

    it('throws_on_timeout', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({
        data: { application_id: 'test-123', status: 'processing' },
      });

      await expect(
        waitForApplicationCompletion('test-123', {
          pollInterval: 10,
          maxAttempts: 2,
        })
      ).rejects.toThrow('Application processing timed out');
    });
  });
});
