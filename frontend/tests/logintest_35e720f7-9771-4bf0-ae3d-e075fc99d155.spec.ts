
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('LoginTest_2026-02-05', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('http://localhost:3004/');

    // Fill input field
    await page.fill('#email', 'test@example.com');

    // Fill input field
    await page.fill('#password', 'test123456');

    // Click element
    await page.click('button[type="submit"]');

    // Click element
    await page.click('button[type="submit"]');

    // Click element
    await page.click('button[type="submit"]');

    // Click element
    await page.click('button[type="submit"]');

    // Click element
    await page.click('button[type="submit"]');
});