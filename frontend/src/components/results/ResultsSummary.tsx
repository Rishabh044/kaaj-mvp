/**
 * Results summary header component.
 */

import { Card } from '../ui';
import type { MatchingResults } from '../../types';

interface ResultsSummaryProps {
  data: MatchingResults;
}

export function ResultsSummary({ data }: ResultsSummaryProps) {
  const eligibilityRate = data.total_evaluated > 0
    ? Math.round((data.total_eligible / data.total_evaluated) * 100)
    : 0;

  return (
    <Card padding="md" className="mb-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-sm font-medium text-gray-500">Lenders Evaluated</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">
            {data.total_evaluated}
          </p>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">Eligible Lenders</p>
          <p
            className="mt-1 text-2xl font-semibold"
            data-testid="eligible-count"
          >
            <span className={data.total_eligible > 0 ? 'text-green-600' : 'text-gray-400'}>
              {data.total_eligible}
            </span>
          </p>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">Eligibility Rate</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">
            {eligibilityRate}%
          </p>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">Best Match</p>
          <p className="mt-1 text-lg font-semibold text-gray-900 truncate">
            {data.best_match?.lender_name || 'None'}
          </p>
        </div>
      </div>
    </Card>
  );
}

export default ResultsSummary;
