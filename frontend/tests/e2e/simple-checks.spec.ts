import { test, expect } from '@playwright/test';

test.describe('Simple Application Checks', () => {

  test('should load login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/GitThink Pulse/);
    await expect(page.getByTestId('login-form')).toBeVisible();
    await expect(page.getByTestId('username-input')).toBeVisible();
    await expect(page.getByTestId('password-input')).toBeVisible();
    await expect(page.getByTestId('login-button')).toBeVisible();
  });

  test('should load dashboard page (unauthenticated)', async ({ page }) => {
    await page.goto('/');
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should login and access dashboard', async ({ page, request }) => {
    // Test API login directly
    const loginResponse = await request.post('http://127.0.0.1:8080/api/auth/login', {
      data: {
        username: 'admin',
        password: 'admin123'
      }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    expect(loginData.success).toBeTruthy();
    expect(loginData.token).toBeTruthy();

    // Test authenticated endpoints
    const statsResponse = await request.get('http://127.0.0.1:8080/api/stats', {
      headers: {
        Authorization: `Bearer ${loginData.token}`
      }
    });

    expect(statsResponse.ok()).toBeTruthy();
    const statsData = await statsResponse.json();
    expect(statsData.total_projects).toBeGreaterThanOrEqual(0);
    expect(statsData.total_reports).toBeGreaterThanOrEqual(0);

    const projectsResponse = await request.get('http://127.0.0.1:8080/api/projects', {
      headers: {
        Authorization: `Bearer ${loginData.token}`
      }
    });

    expect(projectsResponse.ok()).toBeTruthy();
    const projectsData = await projectsResponse.json();
    expect(Array.isArray(projectsData)).toBeTruthy();
  });

  test('should verify all public API endpoints are accessible', async ({ request }) => {
    // Health check
    const healthRes = await request.get('http://127.0.0.1:8080/api/health');
    expect(healthRes.ok()).toBeTruthy();

    // Login (public endpoint)
    const loginRes = await request.post('http://127.0.0.1:8080/api/auth/login', {
      data: { username: 'invalid', password: 'invalid' }
    });
    expect(loginRes.status()).toBe(401); // Should return 401 for invalid credentials
  });

  test('should serve static assets correctly', async ({ page }) => {
    await page.goto('/');

    // Should have root element
    await expect(page.locator('#root')).toBeVisible();
  });
});
