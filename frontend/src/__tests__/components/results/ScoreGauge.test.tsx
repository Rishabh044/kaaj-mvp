/**
 * Tests for the ScoreGauge component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreGauge } from '../../../components/results';

describe('ScoreGauge', () => {
  it('renders_score_value', () => {
    render(<ScoreGauge score={85} />);

    expect(screen.getByText('85')).toBeInTheDocument();
  });

  it('shows_green_for_high_score', () => {
    render(<ScoreGauge score={85} />);

    const gauge = screen.getByText('85');
    expect(gauge.className).toContain('text-green');
  });

  it('shows_blue_for_medium_score', () => {
    render(<ScoreGauge score={65} />);

    const gauge = screen.getByText('65');
    expect(gauge.className).toContain('text-blue');
  });

  it('shows_yellow_for_low_score', () => {
    render(<ScoreGauge score={45} />);

    const gauge = screen.getByText('45');
    expect(gauge.className).toContain('text-yellow');
  });

  it('shows_gray_for_zero_score', () => {
    render(<ScoreGauge score={0} />);

    const gauge = screen.getByText('0');
    expect(gauge.className).toContain('text-gray');
  });

  it('handles_different_sizes', () => {
    const { rerender } = render(<ScoreGauge score={50} size="sm" />);
    expect(screen.getByText('50').className).toContain('h-8');

    rerender(<ScoreGauge score={50} size="lg" />);
    expect(screen.getByText('50').className).toContain('h-16');
  });
});
