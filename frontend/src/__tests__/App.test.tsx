import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App', () => {
  it('renders the welcome message', () => {
    render(<App />);
    expect(
      screen.getByText('Welcome to the Lender Matching Platform')
    ).toBeInTheDocument();
  });

  it('renders the header', () => {
    render(<App />);
    expect(screen.getByText('Lender Matching Platform')).toBeInTheDocument();
  });
});
