import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';

test.describe('Authentication', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.navigateTo('/login');
  });

  test('should display login page correctly', async () => {
    await expect(loginPage.loginForm).toBeVisible();
    await expect(loginPage.usernameInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
    await loginPage.takeScreenshot('login-page');
  });

  test('should not login with empty fields', async ({ page }) => {
    await loginPage.clickElement(loginPage.loginButton);
    await page.waitForTimeout(1000);
    await expect(page).toHaveURL(/\/login/);
  });

  test('should login with valid credentials', async ({ page }) => {
    await loginPage.login('admin', 'admin123');

    await page.waitForURL('/', { timeout: 10000 });
    await expect(page).toHaveURL('/');
    await loginPage.takeScreenshot('dashboard-after-login');
  });

  test('should logout successfully', async ({ page }) => {
    await loginPage.login('admin', 'admin123');
    await page.waitForURL('/', { timeout: 10000 });

    const logoutButton = page.getByTestId('logout-button');
    await expect(logoutButton).toBeVisible();
    await logoutButton.click();

    await page.waitForURL('/login', { timeout: 10000 });
    await expect(page).toHaveURL(/\/login/);
    await loginPage.takeScreenshot('login-after-logout');
  });
});
