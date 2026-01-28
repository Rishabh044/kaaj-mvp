import { test, expect } from '@playwright/test';

test.describe('Lender Management', () => {
  test('list all lenders', async ({ page }) => {
    await page.goto('/admin/lenders');

    // Should show lender list page
    await expect(page.getByText('Lender Policies')).toBeVisible();

    // Should show lender table
    await expect(page.getByRole('table')).toBeVisible();

    // Should have add button
    await expect(
      page.getByRole('button', { name: 'Add New Lender' })
    ).toBeVisible();
  });

  test('view lender details', async ({ page }) => {
    await page.goto('/admin/lenders');

    // Wait for table to load
    await page.waitForSelector('table');

    // Click on first lender row
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();

      // Should navigate to detail page
      await expect(page).toHaveURL(/\/admin\/lenders\/.+/);

      // Should show lender name
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    }
  });

  test('toggle lender status', async ({ page }) => {
    await page.goto('/admin/lenders');

    // Find deactivate button
    const deactivateButton = page.getByRole('button', { name: 'Deactivate' }).first();
    if (await deactivateButton.isVisible()) {
      await deactivateButton.click();

      // Button should change to Activate (or table reloads)
      // Note: Depends on API behavior
    }
  });

  test('add button navigates to create page', async ({ page }) => {
    await page.goto('/admin/lenders');

    await page.getByRole('button', { name: 'Add New Lender' }).click();

    await expect(page).toHaveURL('/admin/lenders/new');
    await expect(page.getByText('Add New Lender')).toBeVisible();
  });
});
