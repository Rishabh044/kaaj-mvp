/**
 * Tests for the ApplicantSection component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ApplicantSection } from '../../../components/application';

describe('ApplicantSection', () => {
  const defaultProps = {
    data: {},
    onChange: vi.fn(),
    errors: {},
  };

  it('renders_all_fields', () => {
    render(<ApplicantSection {...defaultProps} />);

    expect(screen.getByLabelText(/FICO Score/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/TransUnion Score/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Experian Score/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Equifax Score/i)).toBeInTheDocument();
    expect(screen.getByText('Homeowner')).toBeInTheDocument();
    expect(screen.getByText('US Citizen')).toBeInTheDocument();
    expect(screen.getByText('Has CDL')).toBeInTheDocument();
  });

  it('validates_fico_required', () => {
    render(
      <ApplicantSection {...defaultProps} errors={{ fico_score: 'FICO score is required' }} />
    );

    expect(screen.getByText('FICO score is required')).toBeInTheDocument();
  });

  it('validates_fico_range', () => {
    const onChange = vi.fn();
    render(<ApplicantSection {...defaultProps} onChange={onChange} />);

    const ficoInput = screen.getByTestId('fico-score');
    fireEvent.change(ficoInput, { target: { value: '720' } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ fico_score: 720 })
    );
  });

  it('homeowner_toggle_works', () => {
    const onChange = vi.fn();
    render(
      <ApplicantSection
        {...defaultProps}
        data={{ is_homeowner: false }}
        onChange={onChange}
      />
    );

    // Find the toggle button and click it
    const homeownerToggle = screen.getByRole('switch', { name: /homeowner/i });
    fireEvent.click(homeownerToggle);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ is_homeowner: true })
    );
  });

  it('citizen_toggle_works', () => {
    const onChange = vi.fn();
    render(
      <ApplicantSection
        {...defaultProps}
        data={{ is_us_citizen: true }}
        onChange={onChange}
      />
    );

    const citizenToggle = screen.getByRole('switch', { name: /us citizen/i });
    fireEvent.click(citizenToggle);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ is_us_citizen: false })
    );
  });

  it('shows_cdl_fields_when_has_cdl', () => {
    render(
      <ApplicantSection {...defaultProps} data={{ has_cdl: true }} />
    );

    expect(screen.getByLabelText(/CDL Years/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Industry Experience/i)).toBeInTheDocument();
  });

  it('hides_cdl_fields_when_no_cdl', () => {
    render(
      <ApplicantSection {...defaultProps} data={{ has_cdl: false }} />
    );

    expect(screen.queryByLabelText(/CDL Years/i)).not.toBeInTheDocument();
  });
});
