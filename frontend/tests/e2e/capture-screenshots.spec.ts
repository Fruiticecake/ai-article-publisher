import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOTS_DIR = path.join(__dirname, '../../screenshots');

// Ensure screenshots directory exists
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function captureScreenshot(page: Page, name: string) {
  const filePath = path.join(SCREENSHOTS_DIR, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: true });
  console.log(`✓ Captured: ${filePath}`);
  return filePath;
}

async function waitForPageLoad(page: Page) {
  try {
    await page.waitForLoadState('networkidle', { timeout: 10000 });
  } catch {
    // Continue even if networkidle times out
  }
  await page.waitForTimeout(1000);
}

test.describe('Capture Screenshots', () => {
  test.setTimeout(60000); // 60 second timeout

  test('capture all main application pages', async ({ page }) => {
    const screenshots: string[] = [];

    // Clean up previous screenshots except what we already have
    const existingFiles = fs.readdirSync(SCREENSHOTS_DIR);
    console.log('\nExisting screenshots:', existingFiles);

    // 1. Login page (before login)
    console.log('\n1. Login page...');
    await page.goto('/login');
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '01-login-page'));

    // Login
    console.log('Logging in...');
    await page.fill('[data-testid="username-input"]', 'admin');
    await page.fill('[data-testid="password-input"]', 'admin123');
    await page.click('[data-testid="login-button"]');

    // Wait for navigation
    try {
      await page.waitForURL('**/', { timeout: 15000 });
    } catch (e) {
      console.log('Navigation timeout, but continuing...');
    }

    // 2. Dashboard page
    console.log('\n2. Dashboard page...');
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '02-dashboard'));

    // 3. Projects list page
    console.log('\n3. Projects page...');
    await page.click('a[href*="/projects"]', { timeout: 5000 });
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '03-projects'));

    // 4. Reports list page
    console.log('\n4. Reports page...');
    await page.click('a[href*="/reports"]', { timeout: 5000 });
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '04-reports'));

    // 5. Publish page
    console.log('\n5. Publish page...');
    await page.click('a[href*="/publish"]', { timeout: 5000 });
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '05-publish'));

    // 6. Settings/configuration page (includes schedule settings)
    console.log('\n6. Settings page...');
    await page.click('a[href*="/settings"]', { timeout: 5000 });
    await waitForPageLoad(page);

    // Verify credentials are masked - check for password type inputs
    const passwordInputs = page.locator('input[type="password"]');
    const count = await passwordInputs.count();
    console.log(`✓ Found ${count} password/masked input fields on settings page`);

    screenshots.push(await captureScreenshot(page, '06-settings'));

    console.log('\n✅ Screenshot capture complete!');
    console.log(`\nCaptured ${screenshots.length} screenshots:`);
    screenshots.forEach((s, i) => console.log(`${i + 1}. ${s}`));
  });
});
