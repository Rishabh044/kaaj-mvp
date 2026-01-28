/**
 * Detailed criteria breakdown table.
 */

import type { CriterionResult } from '../../types';

interface CriteriaBreakdownProps {
  criteria: CriterionResult[];
}

export function CriteriaBreakdown({ criteria }: CriteriaBreakdownProps) {
  if (!criteria || criteria.length === 0) {
    return (
      <p className="text-sm text-gray-500">No criteria details available.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Criterion
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Required
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actual
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {criteria.map((criterion, index) => (
            <tr key={`${criterion.rule_name}-${index}`}>
              <td className="px-4 py-2 text-sm text-gray-900">
                {formatRuleName(criterion.rule_name)}
              </td>
              <td className="px-4 py-2 text-sm text-gray-500">
                {criterion.required_value}
              </td>
              <td className="px-4 py-2 text-sm text-gray-500">
                {criterion.actual_value}
              </td>
              <td className="px-4 py-2">
                {criterion.passed ? (
                  <span className="inline-flex items-center text-green-600">
                    <svg
                      className="h-4 w-4 mr-1"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Pass
                  </span>
                ) : (
                  <span className="inline-flex items-center text-red-600">
                    <svg
                      className="h-4 w-4 mr-1"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Fail
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatRuleName(ruleName: string): string {
  // Convert snake_case to Title Case
  return ruleName
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default CriteriaBreakdown;
