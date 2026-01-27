/**
 * Main matching results container component.
 */

import { useState, useEffect } from 'react';
import { ResultsSummary } from './ResultsSummary';
import { LenderCard } from './LenderCard';
import { Button } from '../ui';
import { getMatchingResults, getApplicationStatus } from '../../api';
import type { MatchingResults as MatchingResultsType, ApplicationStatus } from '../../types';

interface MatchingResultsProps {
  applicationId: string;
}

export function MatchingResults({ applicationId }: MatchingResultsProps) {
  const [status, setStatus] = useState<ApplicationStatus | null>(null);
  const [results, setResults] = useState<MatchingResultsType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showIneligible, setShowIneligible] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let pollInterval: NodeJS.Timeout | null = null;

    const fetchStatus = async () => {
      try {
        const statusData = await getApplicationStatus(applicationId);
        if (!isMounted) return;

        setStatus(statusData);

        if (statusData.status === 'completed') {
          // Fetch results
          const resultsData = await getMatchingResults(applicationId);
          if (!isMounted) return;
          setResults(resultsData);
          setIsLoading(false);

          // Clear polling
          if (pollInterval) {
            clearInterval(pollInterval);
          }
        } else if (statusData.status === 'error') {
          setError('Application processing failed. Please try again.');
          setIsLoading(false);
          if (pollInterval) {
            clearInterval(pollInterval);
          }
        }
      } catch (err) {
        if (!isMounted) return;
        // If not found or error, try to get results directly
        try {
          const resultsData = await getMatchingResults(applicationId);
          if (!isMounted) return;
          setResults(resultsData);
          setIsLoading(false);
        } catch {
          setError('Failed to load results. Please refresh the page.');
          setIsLoading(false);
        }
      }
    };

    // Initial fetch
    fetchStatus();

    // Poll if still processing
    pollInterval = setInterval(fetchStatus, 3000);

    return () => {
      isMounted = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [applicationId]);

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent"></div>
        <p className="mt-4 text-gray-600">
          {status?.status === 'processing'
            ? 'Evaluating lender matches...'
            : 'Loading results...'}
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="rounded-md bg-red-50 p-4 max-w-md mx-auto">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No results available.</p>
      </div>
    );
  }

  const eligibleMatches = results.matches.filter((m) => m.is_eligible);
  const ineligibleMatches = results.matches.filter((m) => !m.is_eligible);

  return (
    <div>
      <ResultsSummary data={results} />

      {/* Eligible Lenders */}
      <div className="mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Eligible Lenders ({eligibleMatches.length})
        </h2>
        {eligibleMatches.length > 0 ? (
          <div className="space-y-4">
            {eligibleMatches.map((match) => (
              <LenderCard
                key={match.lender_id}
                match={match}
                isBestMatch={match.lender_id === results.best_match?.lender_id}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-md bg-yellow-50 p-4">
            <p className="text-sm text-yellow-700">
              No eligible lenders found for this application. Review the
              ineligible lenders below to understand the rejection reasons.
            </p>
          </div>
        )}
      </div>

      {/* Ineligible Lenders */}
      {ineligibleMatches.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              Ineligible Lenders ({ineligibleMatches.length})
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowIneligible(!showIneligible)}
            >
              {showIneligible ? 'Hide' : 'Show'}
            </Button>
          </div>
          {showIneligible && (
            <div className="space-y-4">
              {ineligibleMatches.map((match) => (
                <LenderCard key={match.lender_id} match={match} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MatchingResults;
