import { chromium, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const BASE_URL = 'http://localhost:8080';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'admin123';

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
  await page.waitForTimeout(1000); // Short wait for animations
}

async function safeClick(page: Page, selector: string) {
  try {
    await page.click(selector, { timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

async function login(page: Page) {
  console.log('Logging in...');
  await page.goto(`${BASE_URL}/login`);
  await page.waitForSelector('[data-testid="username-input"]', { timeout: 10000 });
  await page.fill('[data-testid="username-input"]', ADMIN_USERNAME);
  await page.fill('[data-testid="password-input"]', ADMIN_PASSWORD);
  await page.click('[data-testid="login-button"]');

  // Wait for navigation
  try {
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  } catch {
    // Maybe it goes to root URL instead
    await page.waitForURL('**/', { timeout: 10000 });
  }
  console.log('✓ Logged in successfully');
}

async function main() {
  console.log('Starting screenshot capture...');
  console.log(`Base URL: ${BASE_URL}`);

  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const screenshots: string[] = [];

  try {
    // 1. Login page (before login)
    console.log('\n1. Login page...');
    await page.goto(`${BASE_URL}/login`);
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '01-login-page'));

    // Login to access authenticated pages
    await login(page);
    await waitForPageLoad(page);

    // 2. Dashboard page
    console.log('\n2. Dashboard page...');
    screenshots.push(await captureScreenshot(page, '02-dashboard'));

    // 3. Projects list page
    console.log('\n3. Projects page...');
    if (!await safeClick(page, 'a[href*="/projects"]')) {
      await page.goto(`${BASE_URL}/projects`);
    }
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '03-projects'));

    // 4. Reports list page
    console.log('\n4. Reports page...');
    if (!await safeClick(page, 'a[href*="/reports"]')) {
      await page.goto(`${BASE_URL}/reports`);
    }
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '04-reports'));

    // 5. Publish page
    console.log('\n5. Publish page...');
    if (!await safeClick(page, 'a[href*="/publish"]')) {
      await page.goto(`${BASE_URL}/publish`);
    }
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '05-publish'));

    // 6. Schedule settings page
    console.log('\n6. Schedule page...');
    if (!await safeClick(page, 'a[href*="/schedule"]')) {
      await page.goto(`${BASE_URL}/schedule`);
    }
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '06-schedule'));

    // 7. Settings/configuration page
    console.log('\n7. Settings page...');
    if (!await safeClick(page, 'a[href*="/settings"]')) {
      await page.goto(`${BASE_URL}/settings`);
    }
    await waitForPageLoad(page);
    screenshots.push(await captureScreenshot(page, '07-settings'));

    console.log('\n✅ Screenshot capture complete!');
    console.log(`\nCaptured ${screenshots.length} screenshots:`);
    screenshots.forEach((s, i) => console.log(`${i + 1}. ${s}`));

  } catch (error) {
    console.error('Error during screenshot capture:', error);
  } finally {
    // Keep browser open for a bit to see
    console.log('\nBrowser will close in 3 seconds...');
    await page.waitForTimeout(3000);
    await browser.close();
  }
}

main().catch(console.error);
