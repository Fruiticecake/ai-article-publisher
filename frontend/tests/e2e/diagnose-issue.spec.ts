import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.join(__dirname, '../../screenshots');

async function captureScreenshot(page: any, name: string) {
  const filePath = path.join(SCREENSHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`✓ Captured: ${filePath}`);
  return filePath;
}

test.describe('Diagnose Blank Page Issue', () => {
  test.setTimeout(120000); // 2 minutes for diagnosis

  test('Complete diagnosis of the blank page issue', async ({ page, context }) => {
    console.log('🔍 Starting complete diagnosis...');

    // 1. Test base URL redirects
    console.log('\n1. Testing base URL redirects:');
    try {
      const response = await page.goto('http://127.0.0.1:8080');
      console.log('   - / URL:', response?.status(), response?.url());
    } catch (e) {
      console.log('   - / URL ERROR:', e);
    }

    // 2. Test accessing /dashboard/ directly
    console.log('\n2. Testing /dashboard URL:');
    try {
      const response = await page.goto('http://127.0.0.1:8080/dashboard');
      console.log('   - /dashboard status:', response?.status());
      console.log('   - Final URL:', page.url());

      await captureScreenshot(page, 'diagnosis-dashboard');

      // Check page content
      const bodyText = await page.locator('body').textContent();
      console.log('   - Body contains text:', bodyText?.substring(0, 200));

      // Check console errors
      const consoleErrors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
          console.log('   - Console error:', msg.text());
        }
      });

      // Wait for page to load and check for errors
      await page.waitForTimeout(5000);
      await captureScreenshot(page, 'diagnosis-dashboard-after-wait');

      if (consoleErrors.length > 0) {
        console.log('   - Found', consoleErrors.length, 'console errors!');
      } else {
        console.log('   - No console errors found');
      }

      // Check if root div has content
      const rootContent = await page.locator('#root').innerHTML();
      console.log('   - #root content length:', rootContent?.length);
      console.log('   - #root content snippet:', rootContent?.substring(0, 500));

    } catch (e) {
      console.log('   - /dashboard ERROR:', e);
    }

    // 3. Test login page directly
    console.log('\n3. Testing /login URL:');
    try {
      const response = await page.goto('http://127.0.0.1:8080/login');
      console.log('   - /login status:', response?.status());
      await captureScreenshot(page, 'diagnosis-login');
    } catch (e) {
      console.log('   - /login ERROR:', e);
    }

    // 4. Check if assets can be loaded
    console.log('\n4. Testing asset loading:');

    // Test main JS file directly from root
    console.log('   - Testing JS asset from /assets/...');
    try {
      const jsResponse = await page.goto('http://127.0.0.1:8080/assets/index-BFCDsWR1.js');
      console.log('     → Status:', jsResponse?.status());
      console.log('     → Content type:', jsResponse?.headers()['content-type']);
    } catch (e) {
      console.log('     → ERROR:', e);
    }

    // Test main JS file from dashboard path
    console.log('   - Testing JS asset from /dashboard/assets/...');
    try {
      const jsResponse2 = await page.goto('http://127.0.0.1:8080/dashboard/assets/index-BFCDsWR1.js');
      console.log('     → Status:', jsResponse2?.status());
    } catch (e) {
      console.log('     → ERROR:', e);
    }

    // Test CSS file
    console.log('   - Testing CSS asset:');
    try {
      const cssResponse = await page.goto('http://127.0.0.1:8080/assets/index-BJtWEoqT.css');
      console.log('     → Status:', cssResponse?.status());
    } catch (e) {
      console.log('     → ERROR:', e);
    }

    // 5. Test API endpoints
    console.log('\n5. Testing API endpoints:');

    const endpoints = [
      '/api/health',
      '/health',
      '/api/auth/login',
    ];

    for (const endpoint of endpoints) {
      try {
        console.log(`   - ${endpoint}:`);
        const apiResponse = await page.goto(`http://127.0.0.1:8080${endpoint}`);
        console.log(`     → Status: ${apiResponse?.status()}`);
        const content = await apiResponse?.text();
        console.log(`     → Content: ${content?.substring(0, 200)}`);
      } catch (e) {
        console.log(`     → ERROR: ${e}`);
      }
    }

    // 6. Try a different approach - let's try to navigate without redirects
    console.log('\n6. Trying alternative access paths:');
    console.log('   - Let\'s test accessing index.html directly:');

    try {
      // Try to see what the server returns for various paths
      const testPaths = [
        '/index.html',
        '/assets',
        '/dashboard/index.html'
      ];

      for (const testPath of testPaths) {
        try {
          const resp = await page.goto(`http://127.0.0.1:8080${testPath}`);
          console.log(`     → ${testPath}:`, resp?.status());
        } catch (e) {
          console.log(`     → ${testPath} ERROR:`, e);
        }
      }
    } catch (e) {
      console.log('   - ERROR:', e);
    }

    console.log('\n✅ Diagnosis complete!');
  });
});
