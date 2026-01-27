/**
 * Tests for the ApplicationForm component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ApplicationForm } from '../../../components/application';

// Mock the API
vi.mock('../../../api', () => ({
  submitApplication: vi.fn(),
}));

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('ApplicationForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders_all_steps', () => {
    renderWithRouter(<ApplicationForm />);

    // Should render step indicators
    expect(screen.getByText('Applicant')).toBeInTheDocument();
    expect(screen.getByText('Business')).toBeInTheDocument();
    expect(screen.getByText('Equipment')).toBeInTheDocument();
    expect(screen.getByText('Credit History')).toBeInTheDocument();
    expect(screen.getByText('Loan Request')).toBeInTheDocument();
  });

  it('starts_at_step_1', () => {
    renderWithRouter(<ApplicationForm />);

    // Should show Applicant section content
    expect(screen.getByText('Applicant Information')).toBeInTheDocument();
    expect(screen.getByLabelText(/FICO Score/i)).toBeInTheDocument();
  });

  it('navigates_to_next_step_when_valid', async () => {
    renderWithRouter(<ApplicationForm />);

    // Fill in required field for step 1
    const ficoInput = screen.getByTestId('fico-score');
    fireEvent.change(ficoInput, { target: { value: '720' } });

    // Click next
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    // Should now show Business section
    await waitFor(() => {
      expect(screen.getByText('Business Information')).toBeInTheDocument();
    });
  });

  it('validates_before_next_step', async () => {
    renderWithRouter(<ApplicationForm />);

    // Don't fill in required field, just click next
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    // Should show error and stay on step 1
    await waitFor(() => {
      expect(screen.getByText('FICO score is required')).toBeInTheDocument();
    });
    expect(screen.getByText('Applicant Information')).toBeInTheDocument();
  });

  it('navigates_back_to_previous_step', async () => {
    renderWithRouter(<ApplicationForm />);

    // Fill in step 1 and go to step 2
    const ficoInput = screen.getByTestId('fico-score');
    fireEvent.change(ficoInput, { target: { value: '720' } });
    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(screen.getByText('Business Information')).toBeInTheDocument();
    });

    // Click previous
    fireEvent.click(screen.getByText('Previous'));

    // Should go back to step 1
    await waitFor(() => {
      expect(screen.getByText('Applicant Information')).toBeInTheDocument();
    });
  });

  it('previous_button_disabled_on_first_step', () => {
    renderWithRouter(<ApplicationForm />);

    const previousButton = screen.getByText('Previous');
    expect(previousButton).toBeDisabled();
  });

  it('shows_submit_button_on_last_step', async () => {
    renderWithRouter(<ApplicationForm />);

    // Navigate through all steps (with minimal valid data)
    // Step 1: Applicant
    fireEvent.change(screen.getByTestId('fico-score'), {
      target: { value: '720' },
    });
    fireEvent.click(screen.getByText('Next'));

    // Step 2: Business
    await waitFor(() => screen.getByTestId('business-name'));
    fireEvent.change(screen.getByTestId('business-name'), {
      target: { value: 'Test Business' },
    });
    fireEvent.change(screen.getByTestId('business-state'), {
      target: { value: 'TX' },
    });
    fireEvent.change(screen.getByTestId('years-in-business'), {
      target: { value: '5' },
    });
    fireEvent.click(screen.getByText('Next'));

    // Step 3: Equipment
    await waitFor(() => screen.getByTestId('equipment-category'));
    fireEvent.change(screen.getByTestId('equipment-category'), {
      target: { value: 'construction' },
    });
    fireEvent.click(screen.getByText('Next'));

    // Step 4: Credit History (no required fields)
    await waitFor(() => screen.getByTestId('has-bankruptcy'));
    fireEvent.click(screen.getByText('Next'));

    // Step 5: Loan Request - should show Submit button
    await waitFor(() => {
      expect(screen.getByText('Submit Application')).toBeInTheDocument();
    });
  });
});
