import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

test.describe('Dashboard', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);

    await loginPage.navigateTo('/login');
    await loginPage.login('admin', 'admin123');
    await page.waitForURL('/', { timeout: 10000 });
  });

  test('should display dashboard with all elements', async () => {
    await expect(dashboardPage.statsCards).toBeVisible();
    await expect(dashboardPage.totalProjectsCard).toBeVisible();
    await expect(dashboardPage.totalReportsCard).toBeVisible();
    await expect(dashboardPage.avgStarsCard).toBeVisible();
    await expect(dashboardPage.systemStatusCard).toBeVisible();
    await expect(dashboardPage.recentProjectsCard).toBeVisible();
    await expect(dashboardPage.recentReportsCard).toBeVisible();

    await dashboardPage.takeScreenshot('dashboard-full');
  });

  test('should show valid statistics', async () => {
    const totalProjects = await dashboardPage.getTotalProjects();
    const totalReports = await dashboardPage.getTotalReports();
    const avgStars = await dashboardPage.getAvgStars();
    const systemStatus = await dashboardPage.getSystemStatus();

    expect(totalProjects).not.toBe('');
    expect(totalReports).not.toBe('');
    expect(avgStars).not.toBe('');
    expect(systemStatus).toContain('正常');

    const projectCount = parseInt(totalProjects);
    const reportCount = parseInt(totalReports);
    const stars = parseFloat(avgStars);

    expect(projectCount).toBeGreaterThanOrEqual(0);
    expect(reportCount).toBeGreaterThanOrEqual(0);
    expect(stars).toBeGreaterThanOrEqual(0);
  });

  test('should display recent projects and reports', async ({ page }) => {
    const projectsList = page.getByTestId('projects-list');
    const reportsList = page.getByTestId('reports-list');

    // Verify elements are attached to DOM (they exist even if empty)
    await expect(projectsList).toBeAttached({ timeout: 10000 });
    await expect(reportsList).toBeAttached({ timeout: 10000 });
    // Projects should be visible since we added test data
    await expect(projectsList).toBeVisible();
  });
});
