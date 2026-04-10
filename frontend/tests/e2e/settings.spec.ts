import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { SettingsPage } from './pages/SettingsPage';

test.describe('Settings', () => {
  let loginPage: LoginPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    settingsPage = new SettingsPage(page);

    await loginPage.navigateTo('/login');
    await loginPage.login('admin', 'admin123');
    await page.waitForURL('/', { timeout: 10000 });
    await page.getByTestId('nav-设置').click();
    await page.waitForURL('/settings', { timeout: 10000 });
  });

  test('should navigate to settings page', async ({ page }) => {
    await expect(page).toHaveURL(/\/settings/);
    await expect(settingsPage.header).toBeVisible();
  });

  test('should display settings page elements', async () => {
    await expect(settingsPage.saveAllButton).toBeVisible();
    await expect(settingsPage.githubConfigCard).toBeVisible();
    await expect(settingsPage.githubTokenInput).toBeVisible();

    await settingsPage.takeScreenshot('settings-page');
  });

  test('should test GitHub configuration section', async () => {
    await expect(settingsPage.githubConfigCard).toBeVisible();
    await expect(settingsPage.githubTokenInput).toBeVisible();
  });

  test('should test save functionality', async () => {
    await expect(settingsPage.saveAllButton).toBeVisible();
    await expect(settingsPage.saveAllButton).not.toBeDisabled();
  });
});
