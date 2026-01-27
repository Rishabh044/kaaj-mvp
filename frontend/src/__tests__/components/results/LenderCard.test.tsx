/**
 * Tests for the LenderCard component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LenderCard } from '../../../components/results';
import type { LenderMatch } from '../../../types';

describe('LenderCard', () => {
  const eligibleMatch: LenderMatch = {
    lender_id: 'test_lender',
    lender_name: 'Test Lender',
    is_eligible: true,
    fit_score: 85,
    rank: 1,
    best_program: 'Standard Program',
    rejection_reasons: [],
    criteria_results: [
      {
        rule_name: 'fico_score',
        passed: true,
        required_value: '650',
        actual_value: '720',
        message: 'FICO score meets minimum',
      },
    ],
  };

  const ineligibleMatch: LenderMatch = {
    lender_id: 'test_lender_2',
    lender_name: 'Another Lender',
    is_eligible: false,
    fit_score: 0,
    rank: null,
    best_program: null,
    rejection_reasons: ['FICO score below minimum', 'State restricted'],
    criteria_results: [
      {
        rule_name: 'fico_score',
        passed: false,
        required_value: '700',
        actual_value: '650',
        message: 'FICO score below minimum',
      },
    ],
  };

  it('renders_lender_name_and_score', () => {
    render(<LenderCard match={eligibleMatch} />);

    expect(screen.getByText('Test Lender')).toBeInTheDocument();
    expect(screen.getByText('85')).toBeInTheDocument();
  });

  it('shows_matched_program', () => {
    render(<LenderCard match={eligibleMatch} />);

    expect(screen.getByText(/Standard Program/)).toBeInTheDocument();
  });

  it('shows_eligible_badge_when_eligible', () => {
    render(<LenderCard match={eligibleMatch} />);

    expect(screen.getByText('Eligible')).toBeInTheDocument();
  });

  it('shows_not_eligible_badge_when_ineligible', () => {
    render(<LenderCard match={ineligibleMatch} />);

    expect(screen.getByText('Not Eligible')).toBeInTheDocument();
  });

  it('shows_rank_badge_when_ranked', () => {
    render(<LenderCard match={eligibleMatch} />);

    expect(screen.getByText('Rank #1')).toBeInTheDocument();
  });

  it('shows_best_match_badge_when_best_match', () => {
    render(<LenderCard match={eligibleMatch} isBestMatch />);

    expect(screen.getByText('Best Match')).toBeInTheDocument();
  });

  it('expands_to_show_details', () => {
    render(<LenderCard match={eligibleMatch} />);

    // Initially collapsed
    expect(screen.queryByText('Criteria Breakdown')).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByText('Test Lender'));

    // Now expanded
    expect(screen.getByText('Criteria Breakdown')).toBeInTheDocument();
  });

  it('shows_rejection_reasons_when_ineligible', () => {
    render(<LenderCard match={ineligibleMatch} />);

    // Expand
    fireEvent.click(screen.getByText('Another Lender'));

    expect(screen.getByText('Rejection Reasons:')).toBeInTheDocument();
    expect(screen.getByText('FICO score below minimum')).toBeInTheDocument();
  });
});
