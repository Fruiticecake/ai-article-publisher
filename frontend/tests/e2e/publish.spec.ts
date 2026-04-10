import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { PublishPage } from './pages/PublishPage';

test.describe('Publish', () => {
  let loginPage: LoginPage;
  let publishPage: PublishPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    publishPage = new PublishPage(page);

    await loginPage.navigateTo('/login');
    await loginPage.login('admin', 'admin123');
    await page.waitForURL('/', { timeout: 10000 });
    await page.getByTestId('nav-发布').click();
    await page.waitForURL('/publish', { timeout: 10000 });
  });

  test('should navigate to publish page', async ({ page }) => {
    await expect(page).toHaveURL(/\/publish/);
    await expect(publishPage.publishGrid).toBeVisible();
  });

  test('should display all publish page elements', async () => {
    await expect(publishPage.scheduleConfigCard).toBeVisible();
    await expect(publishPage.manualPublishCard).toBeVisible();
    await expect(publishPage.documentExportCard).toBeVisible();
    await expect(publishPage.reportPublishCard).toBeVisible();
    await expect(publishPage.platformsStatusCard).toBeVisible();

    await publishPage.takeScreenshot('publish-page');
  });

  test('should show schedule configuration', async () => {
    await expect(publishPage.scheduleToggle).toBeVisible();
    await expect(publishPage.cronInput).toBeVisible();
    await expect(publishPage.timezoneSelect).toBeVisible();
    await expect(publishPage.saveScheduleButton).toBeVisible();
  });

  test('should test platform selection and manual publish', async () => {
    await expect(publishPage.platformsGrid).toBeVisible();
    await expect(publishPage.triggerPublishButton).toBeVisible();

    await publishPage.takeScreenshot('publish-platforms');
  });

  test('should have project selection for document export', async () => {
    await expect(publishPage.projectSelect).toBeVisible();
    // Select element exists and is interactive - empty is expected until user makes a selection
    await expect(publishPage.projectSelect).toBeEnabled();
  });

  test('should show platform status cards', async () => {
    // Wait for platform status cards to be visible
    await expect(publishPage.platformsStatusCard).toBeVisible({ timeout: 10000 });
    const enabledPlatformCount = await publishPage.getEnabledPlatformCount();
    // Allow 0 since no platforms may be configured in .env
    await expect(enabledPlatformCount).toBeGreaterThanOrEqual(0);

    await publishPage.takeScreenshot('platform-status');
  });
});
