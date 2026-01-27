/**
 * Tests for the CreditHistorySection component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CreditHistorySection } from '../../../components/application';

describe('CreditHistorySection', () => {
  const defaultProps = {
    data: {},
    onChange: vi.fn(),
    errors: {},
  };

  it('renders_all_flags', () => {
    render(<CreditHistorySection {...defaultProps} />);

    expect(screen.getByText('Bankruptcy')).toBeInTheDocument();
    expect(screen.getByText('Open Judgements')).toBeInTheDocument();
    expect(screen.getByText('Foreclosure')).toBeInTheDocument();
    expect(screen.getByText('Repossession')).toBeInTheDocument();
    expect(screen.getByText('Tax Liens')).toBeInTheDocument();
  });

  it('bankruptcy_shows_details_when_yes', () => {
    render(
      <CreditHistorySection {...defaultProps} data={{ has_bankruptcy: true }} />
    );

    expect(screen.getByLabelText(/Years Since Discharge/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Bankruptcy Chapter/i)).toBeInTheDocument();
  });

  it('bankruptcy_hides_details_when_no', () => {
    render(
      <CreditHistorySection {...defaultProps} data={{ has_bankruptcy: false }} />
    );

    expect(
      screen.queryByLabelText(/Years Since Discharge/i)
    ).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText(/Bankruptcy Chapter/i)
    ).not.toBeInTheDocument();
  });

  it('judgement_shows_amount_when_yes', () => {
    render(
      <CreditHistorySection
        {...defaultProps}
        data={{ has_open_judgements: true }}
      />
    );

    expect(screen.getByLabelText(/Total Judgement Amount/i)).toBeInTheDocument();
  });

  it('all_toggles_work_independently', () => {
    const onChange = vi.fn();
    render(<CreditHistorySection {...defaultProps} onChange={onChange} />);

    const bankruptcyToggle = screen.getByRole('switch', { name: /bankruptcy/i });
    fireEvent.click(bankruptcyToggle);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ has_bankruptcy: true })
    );
  });

  it('shows_clean_history_notice_when_no_issues', () => {
    render(
      <CreditHistorySection
        {...defaultProps}
        data={{
          has_bankruptcy: false,
          has_open_judgements: false,
          has_foreclosure: false,
          has_repossession: false,
          has_tax_liens: false,
        }}
      />
    );

    expect(
      screen.getByText('No derogatory credit history items reported.')
    ).toBeInTheDocument();
  });

  it('hides_clean_history_notice_when_has_issues', () => {
    render(
      <CreditHistorySection {...defaultProps} data={{ has_bankruptcy: true }} />
    );

    expect(
      screen.queryByText('No derogatory credit history items reported.')
    ).not.toBeInTheDocument();
  });
});
