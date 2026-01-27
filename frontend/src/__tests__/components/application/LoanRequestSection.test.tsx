/**
 * Tests for the LoanRequestSection component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LoanRequestSection } from '../../../components/application';

describe('LoanRequestSection', () => {
  const defaultProps = {
    data: {},
    onChange: vi.fn(),
    errors: {},
  };

  it('renders_all_fields', () => {
    render(<LoanRequestSection {...defaultProps} />);

    expect(screen.getByLabelText(/Loan Amount/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Requested Term/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Transaction Type/i)).toBeInTheDocument();
    expect(screen.getByText('Private Party Sale')).toBeInTheDocument();
    expect(screen.getByLabelText(/Down Payment Percentage/i)).toBeInTheDocument();
  });

  it('validates_loan_amount_required', () => {
    render(
      <LoanRequestSection
        {...defaultProps}
        errors={{ amount: 'Loan amount is required' }}
      />
    );

    expect(screen.getByText('Loan amount is required')).toBeInTheDocument();
  });

  it('transaction_type_dropdown_works', () => {
    const onChange = vi.fn();
    render(<LoanRequestSection {...defaultProps} onChange={onChange} />);

    const transactionSelect = screen.getByTestId('transaction-type');
    fireEvent.change(transactionSelect, { target: { value: 'refinance' } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ transaction_type: 'refinance' })
    );
  });

  it('private_party_toggle_works', () => {
    const onChange = vi.fn();
    render(
      <LoanRequestSection
        {...defaultProps}
        data={{ is_private_party: false }}
        onChange={onChange}
      />
    );

    const privatePartyToggle = screen.getByRole('switch', {
      name: /private party/i,
    });
    fireEvent.click(privatePartyToggle);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ is_private_party: true })
    );
  });

  it('down_payment_accepts_decimal', () => {
    const onChange = vi.fn();
    render(<LoanRequestSection {...defaultProps} onChange={onChange} />);

    const downPaymentInput = screen.getByLabelText(/Down Payment Percentage/i);
    fireEvent.change(downPaymentInput, { target: { value: '10.5' } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ down_payment_percent: 10.5 })
    );
  });

  it('shows_amount_display_when_amount_entered', () => {
    render(
      <LoanRequestSection {...defaultProps} data={{ amount: 5000000 }} />
    );

    expect(screen.getByText(/Requested amount:/)).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
  });

  it('shows_financing_summary_with_down_payment', () => {
    render(
      <LoanRequestSection
        {...defaultProps}
        data={{ amount: 5000000, down_payment_percent: 10 }}
      />
    );

    expect(screen.getByText('Financing Summary')).toBeInTheDocument();
    expect(screen.getByText('Down Payment')).toBeInTheDocument();
    expect(screen.getByText('Amount to Finance')).toBeInTheDocument();
  });
});
