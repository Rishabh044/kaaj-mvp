/**
 * Tests for the LenderTable component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LenderTable } from '../../../components/admin';
import type { LenderSummary } from '../../../types';

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('LenderTable', () => {
  const mockLenders: LenderSummary[] = [
    {
      id: 'lender_1',
      name: 'First Lender',
      version: 1,
      program_count: 3,
      is_active: true,
    },
    {
      id: 'lender_2',
      name: 'Second Lender',
      version: 2,
      program_count: 5,
      is_active: false,
    },
  ];

  it('renders_all_lenders', () => {
    renderWithRouter(<LenderTable lenders={mockLenders} />);

    expect(screen.getByText('First Lender')).toBeInTheDocument();
    expect(screen.getByText('Second Lender')).toBeInTheDocument();
  });

  it('shows_program_count', () => {
    renderWithRouter(<LenderTable lenders={mockLenders} />);

    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('shows_status_badge', () => {
    renderWithRouter(<LenderTable lenders={mockLenders} />);

    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('shows_version', () => {
    renderWithRouter(<LenderTable lenders={mockLenders} />);

    expect(screen.getByText('v1')).toBeInTheDocument();
    expect(screen.getByText('v2')).toBeInTheDocument();
  });

  it('calls_toggle_status_on_button_click', () => {
    const onToggleStatus = vi.fn();
    renderWithRouter(
      <LenderTable lenders={mockLenders} onToggleStatus={onToggleStatus} />
    );

    const deactivateButton = screen.getByRole('button', { name: 'Deactivate' });
    fireEvent.click(deactivateButton);

    expect(onToggleStatus).toHaveBeenCalledWith('lender_1');
  });

  it('shows_empty_state_when_no_lenders', () => {
    renderWithRouter(<LenderTable lenders={[]} />);

    expect(screen.getByText('No lenders configured yet.')).toBeInTheDocument();
  });
});
