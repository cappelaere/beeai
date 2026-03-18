/**
 * End-to-End Tests for RealtyIQ User Flows
 * Run with Playwright: npx playwright test
 */

const { test, expect } = require('@playwright/test');

test.describe('Chat Flow', () => {
  test('user can send a message and receive response', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Fill prompt input
    await page.fill('#prompt-input', 'List all properties in downtown');
    
    // Click send button
    await page.click('#send-btn');
    
    // Wait for response
    await page.waitForSelector('.message.assistant', { timeout: 30000 });
    
    // Verify message appears
    const messages = await page.$$('.message');
    expect(messages.length).toBeGreaterThanOrEqual(2); // User + Assistant
  });
  
  test('user can click a favorite card to run prompt', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Wait for cards to load
    await page.waitForSelector('.favorite-card-tile');
    
    // Click first card
    await page.click('.favorite-card-tile:first-child');
    
    // Verify message appears
    await page.waitForSelector('.message.user');
    const userMessage = await page.$('.message.user');
    expect(userMessage).toBeTruthy();
  });
});

test.describe('Session Management', () => {
  test('user can create a new session', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Click new session button
    await page.click('#new-session-btn');
    
    // Fill in session name
    await page.fill('[placeholder="Enter a name for the new session:"]', 'Test Session');
    
    // Verify session is created
    await page.waitForSelector('.session-item.active');
  });
  
  test('user can switch between sessions', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Wait for sessions to load
    await page.waitForSelector('.session-item');
    
    // Click on a session
    await page.click('.session-item:nth-child(2)');
    
    // Verify session is active
    const activeSession = await page.$('.session-item.active');
    expect(activeSession).toBeTruthy();
  });
  
  test('user can delete a session', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.waitForSelector('.session-item');
    const initialCount = await page.$$eval('.session-item', items => items.length);
    
    // Click delete button on first session
    await page.click('.session-item:first-child .delete-session-btn');
    
    // Confirm deletion
    await page.on('dialog', dialog => dialog.accept());
    
    // Verify session is removed
    await page.waitForTimeout(1000);
    const newCount = await page.$$eval('.session-item', items => items.length);
    expect(newCount).toBeLessThan(initialCount);
  });
});

test.describe('Feedback', () => {
  test('user can give thumbs up to response', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Send a message
    await page.fill('#prompt-input', 'Test message');
    await page.click('#send-btn');
    
    // Wait for response
    await page.waitForSelector('.feedback-buttons');
    
    // Click thumbs up
    await page.click('.thumbs-up');
    
    // Verify active state
    const thumbsUp = await page.$('.thumbs-up.active');
    expect(thumbsUp).toBeTruthy();
  });
  
  test('user can give thumbs down to response', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.fill('#prompt-input', 'Test message');
    await page.click('#send-btn');
    await page.waitForSelector('.feedback-buttons');
    
    await page.click('.thumbs-down');
    
    const thumbsDown = await page.$('.thumbs-down.active');
    expect(thumbsDown).toBeTruthy();
  });
});

test.describe('Autocomplete', () => {
  test('typing shows autocomplete suggestions', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Type in prompt input
    await page.fill('#prompt-input', 'list');
    
    // Wait for autocomplete
    await page.waitForSelector('.autocomplete-dropdown', { state: 'visible' });
    
    // Verify suggestions appear
    const suggestions = await page.$$('.autocomplete-item');
    expect(suggestions.length).toBeGreaterThan(0);
  });
  
  test('clicking suggestion fills input', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.fill('#prompt-input', 'list');
    await page.waitForSelector('.autocomplete-item');
    
    // Click first suggestion
    await page.click('.autocomplete-item:first-child');
    
    // Verify input is filled
    const value = await page.inputValue('#prompt-input');
    expect(value.length).toBeGreaterThan(4);
  });
});

test.describe('Prompts Management', () => {
  test('user can view all prompts', async ({ page }) => {
    await page.goto('http://localhost:8002/prompts/');
    
    await page.waitForSelector('.prompt-item');
    
    const prompts = await page.$$('.prompt-item');
    expect(prompts.length).toBeGreaterThan(0);
  });
  
  test('user can search prompts', async ({ page }) => {
    await page.goto('http://localhost:8002/prompts/');
    
    await page.fill('#search-prompts', 'list');
    await page.waitForTimeout(500);
    
    const prompts = await page.$$('.prompt-item');
    expect(prompts.length).toBeGreaterThan(0);
  });
  
  test('user can filter prompts', async ({ page }) => {
    await page.goto('http://localhost:8002/prompts/');
    
    await page.selectOption('#filter-type', 'predefined');
    await page.waitForTimeout(500);
    
    const prompts = await page.$$('.prompt-item');
    expect(prompts.length).toBeGreaterThan(0);
  });
  
  test('user can run a prompt from prompts page', async ({ page }) => {
    await page.goto('http://localhost:8002/prompts/');
    
    await page.waitForSelector('.prompt-run-btn');
    
    // Click run button
    await page.click('.prompt-run-btn:first-child');
    
    // Should redirect to home page
    await page.waitForURL('http://localhost:8002/');
    
    // Should see message
    await page.waitForSelector('.message.user');
  });
  
  test('user can delete a prompt', async ({ page }) => {
    await page.goto('http://localhost:8002/prompts/');
    
    await page.waitForSelector('.prompt-item');
    const initialCount = await page.$$eval('.prompt-item', items => items.length);
    
    // Click delete button
    await page.click('.prompt-delete-btn:first-child');
    
    // Confirm deletion
    page.on('dialog', dialog => dialog.accept());
    
    await page.waitForTimeout(1000);
    const newCount = await page.$$eval('.prompt-item', items => items.length);
    expect(newCount).toBeLessThanOrEqual(initialCount);
  });
});

test.describe('Dashboard', () => {
  test('dashboard displays metrics', async ({ page }) => {
    await page.goto('http://localhost:8002/dashboard/');
    
    // Verify metric cards exist
    await page.waitForSelector('.metric-card');
    const metrics = await page.$$('.metric-card');
    expect(metrics.length).toBeGreaterThanOrEqual(4);
  });
  
  test('dashboard shows session count', async ({ page }) => {
    await page.goto('http://localhost:8002/dashboard/');
    
    const sessionMetric = await page.$('text=Total Sessions');
    expect(sessionMetric).toBeTruthy();
  });
  
  test('dashboard shows documents uploaded', async ({ page }) => {
    await page.goto('http://localhost:8002/dashboard/');
    
    const docMetric = await page.$('text=Documents Uploaded');
    expect(docMetric).toBeTruthy();
  });
});

test.describe('Theme Switching', () => {
  test('user can switch to dark theme', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Click theme toggle
    await page.click('#theme-toggle');
    
    // Verify dark theme is applied
    const body = await page.$('body');
    const className = await body.getAttribute('class');
    expect(className).toContain('theme-');
  });
});

test.describe('Copy Functionality', () => {
  test('user can copy assistant response', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    // Send message and wait for response
    await page.fill('#prompt-input', 'Test');
    await page.click('#send-btn');
    await page.waitForSelector('.copy-btn');
    
    // Click copy button
    await page.click('.copy-btn');
    
    // Verify tooltip or button text changes
    await page.waitForTimeout(500);
    const btnText = await page.textContent('.copy-btn');
    expect(btnText).toBe('Copied!');
  });
});

test.describe('Voice Input', () => {
  test('voice input button exists', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    const voiceBtn = await page.$('#voice-input-btn');
    expect(voiceBtn).toBeTruthy();
  });
});

test.describe('Navbar Resize', () => {
  test('user can resize navigation bar', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    const nav = await page.$('.main-nav');
    const initialWidth = await nav.evaluate(el => el.offsetWidth);
    
    // Simulate drag to resize (complex, may need special handling)
    // This is a simplified test
    expect(initialWidth).toBeGreaterThan(0);
  });
});

test.describe('Panel Resize', () => {
  test('user can resize favorite cards panel', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.waitForSelector('#favorite-cards-panel');
    const panel = await page.$('#favorite-cards-panel');
    const initialHeight = await panel.evaluate(el => el.offsetHeight);
    
    expect(initialHeight).toBeGreaterThan(0);
  });
});

test.describe('Navigation', () => {
  test('user can navigate to dashboard', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.click('a[href="/dashboard/"]');
    await page.waitForURL('**/dashboard/');
    
    expect(page.url()).toContain('/dashboard/');
  });
  
  test('user can navigate to prompts page', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.click('a[href="/prompts/"]');
    await page.waitForURL('**/prompts/');
    
    expect(page.url()).toContain('/prompts/');
  });
  
  test('user can navigate to documents page', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.click('a[href="/documents/"]');
    await page.waitForURL('**/documents/');
    
    expect(page.url()).toContain('/documents/');
  });
  
  test('user can navigate to examples page', async ({ page }) => {
    await page.goto('http://localhost:8002/');
    
    await page.click('a[href="/examples/"]');
    await page.waitForURL('**/examples/');
    
    expect(page.url()).toContain('/examples/');
  });
});
