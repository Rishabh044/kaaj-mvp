import { test, expect } from '@playwright/test';

test.describe('Edge Cases', () => {
  test.describe('California Applicant', () => {
    test('CA state shows in dropdown and can be selected', async ({ page }) => {
      await page.goto('/apply');

      // Go to business section
      await page.getByTestId('fico-score').fill('720');
      await page.getByRole('button', { name: 'Next' }).click();

      // Select California
      await page.getByTestId('business-state').selectOption('CA');

      // Verify selection
      await expect(page.getByTestId('business-state')).toHaveValue('CA');
    });
  });

  test.describe('Startup Business', () => {
    test('accepts low years in business', async ({ page }) => {
      await page.goto('/apply');

      // Go to business section
      await page.getByTestId('fico-score').fill('720');
      await page.getByRole('button', { name: 'Next' }).click();

      // Fill with startup values
      await page.getByTestId('business-name').fill('New Startup LLC');
      await page.getByTestId('business-state').selectOption('TX');
      await page.getByTestId('years-in-business').fill('0.5');

      // Should accept and allow next
      await page.getByRole('button', { name: 'Next' }).click();
      await expect(page.getByText('Equipment Information')).toBeVisible();
    });
  });

  test.describe('High Mileage Truck', () => {
    test('accepts high mileage values', async ({ page }) => {
      await page.goto('/apply');

      // Navigate through form
      await page.getByTestId('fico-score').fill('720');
      await page.getByRole('button', { name: 'Next' }).click();

      await page.getByTestId('business-name').fill('Test Business');
      await page.getByTestId('business-state').selectOption('TX');
      await page.getByTestId('years-in-business').fill('5');
      await page.getByRole('button', { name: 'Next' }).click();

      // Equipment section - high mileage truck
      await page.getByTestId('equipment-category').selectOption('class_8_truck');
      await page.getByTestId('equipment-year').fill('2018');
      await page.getByTestId('equipment-mileage').fill('800000');

      // Should show mileage and allow proceeding
      await expect(page.getByTestId('equipment-mileage')).toHaveValue('800000');
    });
  });

  test.describe('Bankruptcy History', () => {
    test('shows bankruptcy details when selected', async ({ page }) => {
      await page.goto('/apply');

      // Navigate to credit history
      await page.getByTestId('fico-score').fill('720');
      await page.getByRole('button', { name: 'Next' }).click();

      await page.getByTestId('business-name').fill('Test Business');
      await page.getByTestId('business-state').selectOption('TX');
      await page.getByTestId('years-in-business').fill('5');
      await page.getByRole('button', { name: 'Next' }).click();

      await page.getByTestId('equipment-category').selectOption('construction');
      await page.getByRole('button', { name: 'Next' }).click();

      // Click bankruptcy toggle
      await page.getByRole('switch', { name: /bankruptcy/i }).click();

      // Should show additional fields
      await expect(page.getByLabelText(/Years Since Discharge/i)).toBeVisible();
      await expect(page.getByLabelText(/Bankruptcy Chapter/i)).toBeVisible();
    });
  });

  test.describe('Trucking Equipment', () => {
    test('shows mileage field for class 8 truck', async ({ page }) => {
      await page.goto('/apply');

      await page.getByTestId('fico-score').fill('720');
      await page.getByRole('button', { name: 'Next' }).click();

      await page.getByTestId('business-name').fill('Test');
      await page.getByTestId('business-state').selectOption('TX');
      await page.getByTestId('years-in-business').fill('5');
      await page.getByRole('button', { name: 'Next' }).click();

      await page.getByTestId('equipment-category').selectOption('class_8_truck');

      await expect(page.getByTestId('equipment-mileage')).toBeVisible();
    });

    test('shows hours field for construction equipment', async ({ page }) => {
      await page.goto('/apply');

      await page.getByTestId('fico-score').fill('720');
      await page.getByRole('button', { name: 'Next' }).click();

      await page.getByTestId('business-name').fill('Test');
      await page.getByTestId('business-state').selectOption('TX');
      await page.getByTestId('years-in-business').fill('5');
      await page.getByRole('button', { name: 'Next' }).click();

      await page.getByTestId('equipment-category').selectOption('construction');

      await expect(page.getByTestId('equipment-hours')).toBeVisible();
    });
  });
});
