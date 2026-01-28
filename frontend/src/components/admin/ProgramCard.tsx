/**
 * Program display card component.
 */

import { Card, Badge } from '../ui';
import type { ProgramDetail } from '../../types';

interface ProgramCardProps {
  program: ProgramDetail;
}

export function ProgramCard({ program }: ProgramCardProps) {
  const formatAmount = (amount: number | null) => {
    if (amount === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount / 100);
  };

  return (
    <Card padding="md">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-md font-medium text-gray-900">{program.name}</h3>
            {program.is_app_only && (
              <Badge variant="warning" size="sm">
                App Only
              </Badge>
            )}
          </div>
          {program.description && (
            <p className="mt-1 text-sm text-gray-500">{program.description}</p>
          )}
        </div>
        <span className="text-xs text-gray-400">{program.id}</span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-4">
        <div>
          <p className="text-xs text-gray-500">Min Amount</p>
          <p className="text-sm font-medium text-gray-900">
            {formatAmount(program.min_amount)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Max Amount</p>
          <p className="text-sm font-medium text-gray-900">
            {formatAmount(program.max_amount)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Max Term</p>
          <p className="text-sm font-medium text-gray-900">
            {program.max_term_months
              ? `${program.max_term_months} months`
              : 'N/A'}
          </p>
        </div>
      </div>

      {program.criteria && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
            Criteria
          </h4>
          <div className="flex flex-wrap gap-2">
            {program.criteria.credit_score && (
              <Badge variant="default" size="sm">
                Credit Score
              </Badge>
            )}
            {program.criteria.business && (
              <Badge variant="default" size="sm">
                Business
              </Badge>
            )}
            {program.criteria.credit_history && (
              <Badge variant="default" size="sm">
                Credit History
              </Badge>
            )}
            {program.criteria.equipment && (
              <Badge variant="default" size="sm">
                Equipment
              </Badge>
            )}
            {program.criteria.geographic && (
              <Badge variant="default" size="sm">
                Geographic
              </Badge>
            )}
            {program.criteria.industry && (
              <Badge variant="default" size="sm">
                Industry
              </Badge>
            )}
            {program.criteria.transaction && (
              <Badge variant="default" size="sm">
                Transaction
              </Badge>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}

export default ProgramCard;
