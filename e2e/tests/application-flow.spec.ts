import { test, expect } from '@playwright/test';

test.describe('Application Flow', () => {
  test('complete application submission and results', async ({ page }) => {
    // Navigate to application form
    await page.goto('/apply');

    // Verify form loads
    await expect(page.getByText('Applicant Information')).toBeVisible();

    // Step 1: Fill Applicant Info
    await page.getByTestId('fico-score').fill('720');
    await page.getByRole('switch', { name: /homeowner/i }).click();
    await page.getByRole('button', { name: 'Next' }).click();

    // Step 2: Fill Business Info
    await expect(page.getByText('Business Information')).toBeVisible();
    await page.getByTestId('business-name').fill('Test Trucking LLC');
    await page.getByTestId('business-state').selectOption('TX');
    await page.getByTestId('years-in-business').fill('5');
    await page.getByRole('button', { name: 'Next' }).click();

    // Step 3: Fill Equipment Info
    await expect(page.getByText('Equipment Information')).toBeVisible();
    await page.getByTestId('equipment-category').selectOption('class_8_truck');
    await page.getByTestId('equipment-year').fill('2022');
    await page.getByTestId('equipment-mileage').fill('50000');
    await page.getByRole('button', { name: 'Next' }).click();

    // Step 4: Credit History (no issues)
    await expect(page.getByText('Credit History')).toBeVisible();
    await page.getByRole('button', { name: 'Next' }).click();

    // Step 5: Loan Request
    await expect(page.getByText('Loan Request')).toBeVisible();
    await page.getByTestId('loan-amount').fill('50000');
    await page.getByTestId('transaction-type').selectOption('purchase');

    // Submit
    await page.getByRole('button', { name: 'Submit Application' }).click();

    // Wait for results page
    await expect(page).toHaveURL(/\/results\//);

    // Verify results displayed
    await expect(page.getByText('Matching Results')).toBeVisible();
    await expect(page.getByTestId('eligible-count')).toBeVisible();
  });

  test('form validation prevents invalid submission', async ({ page }) => {
    await page.goto('/apply');

    // Try to proceed without filling required fields
    await page.getByRole('button', { name: 'Next' }).click();

    // Should show error
    await expect(page.getByText('FICO score is required')).toBeVisible();

    // Fill with invalid value
    await page.getByTestId('fico-score').fill('200');
    await page.getByRole('button', { name: 'Next' }).click();

    // Should show range error
    await expect(
      page.getByText('FICO score must be between 300 and 850')
    ).toBeVisible();
  });

  test('form navigation preserves data', async ({ page }) => {
    await page.goto('/apply');

    // Fill step 1
    await page.getByTestId('fico-score').fill('720');
    await page.getByRole('button', { name: 'Next' }).click();

    // Fill step 2
    await page.getByTestId('business-name').fill('Test Business');
    await page.getByTestId('business-state').selectOption('TX');
    await page.getByTestId('years-in-business').fill('5');

    // Go back
    await page.getByRole('button', { name: 'Previous' }).click();

    // Verify step 1 data is preserved
    await expect(page.getByTestId('fico-score')).toHaveValue('720');

    // Go forward again
    await page.getByRole('button', { name: 'Next' }).click();

    // Verify step 2 data is preserved
    await expect(page.getByTestId('business-name')).toHaveValue('Test Business');
  });
});
