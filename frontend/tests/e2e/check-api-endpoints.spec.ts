import { test, expect } from '@playwright/test';

test.describe('API Endpoints Check', () => {
  test.setTimeout(60000);

  const baseUrl = 'http://127.0.0.1:8080';
  const apiEndpoints = [
    {
      name: 'Health check',
      path: '/api/health',
      method: 'GET',
      expectedStatus: 200,
    },
    {
      name: 'Get projects',
      path: '/api/projects',
      method: 'GET',
      expectedStatus: 200,
      needsAuth: true,
    },
    {
      name: 'Get reports',
      path: '/api/reports',
      method: 'GET',
      expectedStatus: 200,
      needsAuth: true,
    },
    {
      name: 'Get publishers',
      path: '/api/publishers',
      method: 'GET',
      expectedStatus: 200,
      needsAuth: true,
    },
    {
      name: 'Get schedule settings',
      path: '/api/settings/schedule',
      method: 'GET',
      expectedStatus: 200,
      needsAuth: true,
    },
    {
      name: 'Get GitHub config',
      path: '/api/settings/github',
      method: 'GET',
      expectedStatus: 200,
      needsAuth: true,
    },
    {
      name: 'Get Claude config',
      path: '/api/settings/claude',
      method: 'GET',
      expectedStatus: 200,
      needsAuth: true,
    },
  ];

  test('Check all API endpoints', async ({ page, request }) => {
    console.log('🔍 Checking API endpoints...');

    // Check public endpoints first
    console.log('\n📡 Public endpoints:');
    const publicEndpoints = apiEndpoints.filter(endpoint => !endpoint.needsAuth);
    for (const endpoint of publicEndpoints) {
      try {
        console.log(`\nChecking ${endpoint.name} (${endpoint.method} ${endpoint.path})...`);

        const response = await request.fetch(baseUrl + endpoint.path, {
          method: endpoint.method,
        });

        console.log(`Status: ${response.status}`);
        const responseText = await response.text();
        console.log(`Response: ${responseText.substring(0, 100)}${responseText.length > 100 ? '...' : ''}`);

        expect(response.status()).toBe(endpoint.expectedStatus);

        console.log('✅ Success');
      } catch (error) {
        console.log(`❌ Error: ${error}`);
        throw error;
      }
    }

    // Login to check protected endpoints
    console.log('\n🔐 Logging in...');
    await page.goto(baseUrl + '/login');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL(baseUrl + '/');

    // Check authenticated endpoints
    console.log('\n🔒 Protected endpoints:');
    const authEndpoints = apiEndpoints.filter(endpoint => endpoint.needsAuth);
    for (const endpoint of authEndpoints) {
      try {
        console.log(`\nChecking ${endpoint.name} (${endpoint.method} ${endpoint.path})...`);

        // Use page context to include cookies for authentication
        const response = await page.request.fetch(baseUrl + endpoint.path, {
          method: endpoint.method,
        });

        console.log(`Status: ${response.status}`);
        const responseText = await response.text();
        console.log(`Response: ${responseText.substring(0, 100)}${responseText.length > 100 ? '...' : ''}`);

        expect(response.status()).toBe(endpoint.expectedStatus);

        console.log('✅ Success');
      } catch (error) {
        console.log(`❌ Error: ${error}`);
        throw error;
      }
    }

    console.log('\n✅ All API endpoints check completed!');
  });
});
