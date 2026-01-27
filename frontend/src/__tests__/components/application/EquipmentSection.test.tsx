/**
 * Tests for the EquipmentSection component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EquipmentSection } from '../../../components/application';

describe('EquipmentSection', () => {
  const defaultProps = {
    data: {},
    onChange: vi.fn(),
    errors: {},
  };

  it('renders_all_fields', () => {
    render(<EquipmentSection {...defaultProps} />);

    expect(screen.getByLabelText(/Equipment Category/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Equipment Type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Year/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Condition/i)).toBeInTheDocument();
  });

  it('category_dropdown_works', () => {
    const onChange = vi.fn();
    render(<EquipmentSection {...defaultProps} onChange={onChange} />);

    const categorySelect = screen.getByTestId('equipment-category');
    fireEvent.change(categorySelect, { target: { value: 'construction' } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ category: 'construction' })
    );
  });

  it('shows_mileage_for_truck', () => {
    render(
      <EquipmentSection {...defaultProps} data={{ category: 'class_8_truck' }} />
    );

    expect(screen.getByTestId('equipment-mileage')).toBeInTheDocument();
  });

  it('shows_mileage_for_trailer', () => {
    render(
      <EquipmentSection {...defaultProps} data={{ category: 'trailer' }} />
    );

    expect(screen.getByTestId('equipment-mileage')).toBeInTheDocument();
  });

  it('shows_hours_for_construction', () => {
    render(
      <EquipmentSection {...defaultProps} data={{ category: 'construction' }} />
    );

    expect(screen.getByTestId('equipment-hours')).toBeInTheDocument();
  });

  it('hides_mileage_for_non_trucking', () => {
    render(
      <EquipmentSection {...defaultProps} data={{ category: 'medical' }} />
    );

    expect(screen.queryByTestId('equipment-mileage')).not.toBeInTheDocument();
  });

  it('validates_year_range', () => {
    render(
      <EquipmentSection
        {...defaultProps}
        errors={{ year: 'Year must be between 1980 and 2027' }}
      />
    );

    expect(
      screen.getByText('Year must be between 1980 and 2027')
    ).toBeInTheDocument();
  });

  it('shows_equipment_age_info', () => {
    const currentYear = new Date().getFullYear();
    render(
      <EquipmentSection {...defaultProps} data={{ year: currentYear - 5 }} />
    );

    expect(screen.getByText(/Equipment age:/)).toBeInTheDocument();
    expect(screen.getByText('5 years')).toBeInTheDocument();
  });
});
