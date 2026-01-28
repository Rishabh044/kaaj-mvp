/**
 * Single lender result card component.
 */

import { useState } from 'react';
import { Card, Badge } from '../ui';
import { ScoreGauge } from './ScoreGauge';
import { CriteriaBreakdown } from './CriteriaBreakdown';
import { RejectionReasons } from './RejectionReasons';
import type { LenderMatch } from '../../types';

interface LenderCardProps {
  match: LenderMatch;
  isBestMatch?: boolean;
}

export function LenderCard({ match, isBestMatch = false }: LenderCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card
      padding="md"
      className={`
        transition-all duration-200
        ${isBestMatch ? 'ring-2 ring-green-500 ring-offset-2' : ''}
        ${!match.is_eligible ? 'opacity-75' : ''}
      `}
    >
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-4">
          <ScoreGauge score={match.fit_score} />
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-medium text-gray-900">
                {match.lender_name}
              </h3>
              {isBestMatch && (
                <Badge variant="success" size="sm">
                  Best Match
                </Badge>
              )}
              {match.rank && (
                <Badge variant="default" size="sm">
                  Rank #{match.rank}
                </Badge>
              )}
            </div>
            {match.best_program && (
              <p className="text-sm text-gray-500">
                Program: {match.best_program}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {match.is_eligible ? (
            <Badge variant="success">Eligible</Badge>
          ) : (
            <Badge variant="error">Not Eligible</Badge>
          )}
          <button
            className="text-gray-400 hover:text-gray-600"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            <svg
              className={`h-5 w-5 transform transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {!match.is_eligible && (
            <RejectionReasons reasons={match.rejection_reasons} />
          )}

          {match.criteria_results && match.criteria_results.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Criteria Breakdown
              </h4>
              <CriteriaBreakdown criteria={match.criteria_results} />
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export default LenderCard;
