/**
 * Tests for the BusinessSection component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BusinessSection } from '../../../components/application';

describe('BusinessSection', () => {
  const defaultProps = {
    data: {},
    onChange: vi.fn(),
    errors: {},
  };

  it('renders_all_fields', () => {
    render(<BusinessSection {...defaultProps} />);

    expect(screen.getByLabelText(/Business Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/State/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Years in Business/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Industry Code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Industry Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Annual Revenue/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Fleet Size/i)).toBeInTheDocument();
  });

  it('validates_business_name_required', () => {
    render(
      <BusinessSection
        {...defaultProps}
        errors={{ name: 'Business name is required' }}
      />
    );

    expect(screen.getByText('Business name is required')).toBeInTheDocument();
  });

  it('state_dropdown_works', () => {
    const onChange = vi.fn();
    render(<BusinessSection {...defaultProps} onChange={onChange} />);

    const stateSelect = screen.getByTestId('business-state');
    fireEvent.change(stateSelect, { target: { value: 'TX' } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ state: 'TX' })
    );
  });

  it('state_dropdown_has_all_states', () => {
    render(<BusinessSection {...defaultProps} />);

    const stateSelect = screen.getByTestId('business-state');
    expect(stateSelect).toBeInTheDocument();

    // Check for a few states
    expect(screen.getByText('Texas')).toBeInTheDocument();
    expect(screen.getByText('California')).toBeInTheDocument();
    expect(screen.getByText('New York')).toBeInTheDocument();
  });

  it('years_in_business_accepts_decimal', () => {
    const onChange = vi.fn();
    render(<BusinessSection {...defaultProps} onChange={onChange} />);

    const yearsInput = screen.getByTestId('years-in-business');
    fireEvent.change(yearsInput, { target: { value: '2.5' } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ years_in_business: 2.5 })
    );
  });
});
