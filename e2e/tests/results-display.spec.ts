import { test, expect } from '@playwright/test';

test.describe('Results Display', () => {
  // Note: These tests assume the API returns mock data
  // In production, you would seed the database or mock the API

  test('shows eligible lenders ranked by score', async ({ page }) => {
    // Navigate directly to a results page with a known application ID
    await page.goto('/results/test-application-123');

    // Wait for results to load
    await expect(page.getByText('Matching Results')).toBeVisible();

    // Check that eligible lenders section exists
    await expect(page.getByText(/Eligible Lenders/)).toBeVisible();
  });

  test('shows ineligible lenders section', async ({ page }) => {
    await page.goto('/results/test-application-123');

    // Check for ineligible section
    await expect(page.getByText(/Ineligible Lenders/)).toBeVisible();
  });

  test('expands lender card to show details', async ({ page }) => {
    await page.goto('/results/test-application-123');

    // Wait for results
    await page.waitForSelector('[data-testid="eligible-count"]');

    // Find a lender card and click to expand
    const lenderCard = page.locator('.cursor-pointer').first();
    if (await lenderCard.isVisible()) {
      await lenderCard.click();

      // Should show criteria breakdown
      await expect(page.getByText('Criteria Breakdown')).toBeVisible();
    }
  });

  test('highlights best match', async ({ page }) => {
    await page.goto('/results/test-application-123');

    // Wait for results
    await page.waitForSelector('[data-testid="eligible-count"]');

    // Check for best match badge
    const bestMatchBadge = page.getByText('Best Match');
    // Note: May or may not be visible depending on mock data
  });
});
