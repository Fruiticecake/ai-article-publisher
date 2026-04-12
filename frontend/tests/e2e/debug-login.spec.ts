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

test.describe('Debug Login Page', () => {
  test.setTimeout(60000);

  test('Debug login page rendering', async ({ page }) => {
    console.log('🔍 Debugging login page...');

    // Go to login page
    await page.goto('http://127.0.0.1:8080/login');
    console.log('✅ Page loaded:', page.url());

    // Capture screenshot immediately
    await captureScreenshot(page, 'debug-login-page-1');

    // Wait for page to load
    await page.waitForLoadState('load');
    await page.waitForTimeout(3000);

    // Check what's in the body
    const bodyHTML = await page.locator('body').innerHTML();
    console.log('Body HTML length:', bodyHTML.length);
    console.log('Body HTML snippet (1000 chars):', bodyHTML.substring(0, 1000));

    // Look for input elements with any selectors
    const inputs = await page.$$('input');
    console.log('Number of input elements found:', inputs.length);

    for (let i = 0; i < inputs.length; i++) {
      const input = inputs[i];
      const type = await input.getAttribute('type');
      const placeholder = await input.getAttribute('placeholder');
      const id = await input.getAttribute('id');
      const testid = await input.getAttribute('data-testid');
      console.log(`Input ${i}: type=${type}, id=${id}, testid=${testid}, placeholder=${placeholder}`);
    }

    // Check for any React-related content
    const reactRoot = await page.locator('#root');
    console.log('Root element exists:', await reactRoot.isVisible());

    if (await reactRoot.isVisible()) {
      const rootHTML = await reactRoot.innerHTML();
      console.log('Root HTML length:', rootHTML.length);
      console.log('Root HTML content:', rootHTML);
    }

    // Capture screenshot again after wait
    await captureScreenshot(page, 'debug-login-page-2');

    console.log('✅ Debug complete');
  });
});
