/**
 * Tests for the CriteriaBreakdown component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CriteriaBreakdown } from '../../../components/results';
import type { CriterionResult } from '../../../types';

describe('CriteriaBreakdown', () => {
  const mockCriteria: CriterionResult[] = [
    {
      rule_name: 'fico_score',
      passed: true,
      required_value: '650',
      actual_value: '720',
      message: 'FICO score meets minimum',
    },
    {
      rule_name: 'time_in_business',
      passed: false,
      required_value: '2 years',
      actual_value: '1.5 years',
      message: 'Time in business below minimum',
    },
  ];

  it('renders_all_criteria', () => {
    render(<CriteriaBreakdown criteria={mockCriteria} />);

    expect(screen.getByText('Fico Score')).toBeInTheDocument();
    expect(screen.getByText('Time In Business')).toBeInTheDocument();
  });

  it('shows_pass_icon_for_passed', () => {
    render(<CriteriaBreakdown criteria={mockCriteria} />);

    expect(screen.getByText('Pass')).toBeInTheDocument();
  });

  it('shows_fail_icon_for_failed', () => {
    render(<CriteriaBreakdown criteria={mockCriteria} />);

    expect(screen.getByText('Fail')).toBeInTheDocument();
  });

  it('shows_required_and_actual_values', () => {
    render(<CriteriaBreakdown criteria={mockCriteria} />);

    expect(screen.getByText('650')).toBeInTheDocument();
    expect(screen.getByText('720')).toBeInTheDocument();
    expect(screen.getByText('2 years')).toBeInTheDocument();
    expect(screen.getByText('1.5 years')).toBeInTheDocument();
  });

  it('handles_empty_criteria', () => {
    render(<CriteriaBreakdown criteria={[]} />);

    expect(screen.getByText('No criteria details available.')).toBeInTheDocument();
  });
});
