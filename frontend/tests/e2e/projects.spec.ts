import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { ProjectsPage } from './pages/ProjectsPage';

test.describe('Projects', () => {
  let loginPage: LoginPage;
  let projectsPage: ProjectsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    projectsPage = new ProjectsPage(page);

    await loginPage.navigateTo('/login');
    await loginPage.login('admin', 'admin123');
    await page.waitForURL('/', { timeout: 10000 });
    await page.getByTestId('nav-项目').click();
    await page.waitForURL('/projects', { timeout: 10000 });
  });

  test('should navigate to projects page', async ({ page }) => {
    await expect(page).toHaveURL(/\/projects/);
    await expect(projectsPage.header).toBeVisible();
  });

  test('should display projects page elements', async () => {
    await expect(projectsPage.searchInput).toBeVisible();
    await expect(projectsPage.filterButton).toBeVisible();
    await expect(projectsPage.projectsCard).toBeVisible();
    await expect(projectsPage.projectsList).toBeVisible();

    await projectsPage.takeScreenshot('projects-page');
  });

  test('should search projects', async () => {
    await projectsPage.searchProjects('test');
    await projectsPage.takeScreenshot('projects-search');
  });

  test('should have at least one project', async () => {
    // Wait for projects to load
    await expect(projectsPage.projectsList).toBeVisible();
    await projectsPage.page.waitForSelector('[data-testid^="project-item-"]', { timeout: 10000 });
    const projectCount = await projectsPage.getProjectCount();
    expect(projectCount).toBeGreaterThan(0);
  });

  test('should have project names', async () => {
    // Wait for projects to load
    await expect(projectsPage.projectsList).toBeVisible();
    await projectsPage.page.waitForSelector('[data-testid^="project-name-"]', { timeout: 10000 });
    const projectNames = await projectsPage.getProjectNames();
    expect(projectNames.length).toBeGreaterThan(0);
    projectNames.forEach(name => {
      expect(name).not.toBe('');
    });
  });
});
