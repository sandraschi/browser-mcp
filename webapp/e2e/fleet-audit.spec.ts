import { expect, test } from '@playwright/test';

const BE = 'http://127.0.0.1:10780';
const ALL_ROUTES = [
  '/',
  '/bookmarks',
  '/tools',
  '/chat',
  '/settings',
  '/help',
  '/api-docs',
  '/apps',
  '/skills',
  '/logs',
];

// Console errors we tolerate: missing favicon and failed asset/network loads
// (dev server quirks), not application errors.
function isBenignConsoleError(text: string): boolean {
  return /favicon|Failed to load resource|net::ERR_|404/i.test(text);
}

test.describe('Fleet Audit', () => {
  test('Backend health returns 200', async ({ request }) => {
    const resp = await request.get(`${BE}/health`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.status).toBe('ok');
    expect(body.tool_count).toBeGreaterThan(0);
  });

  test('Backend status is rich', async ({ request }) => {
    const resp = await request.get(`${BE}/api/status`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.service).toBe('browser-mcp');
    expect(body.browsers).toBeDefined();
    expect(body.bookmarks_sources).toBeDefined();
    expect(body.llm).toBeDefined();
  });

  test('Backend shutdown requires confirm', async ({ request }) => {
    const resp = await request.post(`${BE}/api/shutdown`);
    expect(resp.status()).toBe(400);
    expect((await resp.json()).status).toBe('error');
  });

  test('Frontend loads without crash or console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`));
    page.on('console', (msg) => {
      if (msg.type() === 'error' && !isBenignConsoleError(msg.text())) errors.push(msg.text());
    });
    await page.goto('/', { timeout: 15000 });
    await expect(page.locator('#root')).toBeAttached();
    await expect(page.getByTestId('kpi-server')).toBeVisible();
    expect(errors).toEqual([]);
  });

  test('Navigation sidebar links all resolve', async ({ page }) => {
    await page.goto('/');
    for (const route of ALL_ROUTES) {
      const label =
        route === '/' ? 'Dashboard' : route === '/api-docs' ? 'API Docs' : route[1].toUpperCase() + route.slice(2);
      await page.getByRole('link', { name: label, exact: true }).first().click();
      await expect(page).toHaveURL(new RegExp(`${route.replace('/', '\\/')}`));
      await expect(page.locator('#root')).toBeAttached();
    }
  });

  test('No 404s across all routes', async ({ page }) => {
    const notFound: string[] = [];
    page.on('response', (r) => {
      if (r.status() >= 400 && !/favicon/i.test(r.url())) notFound.push(`${r.status()} ${r.url()}`);
    });
    for (const route of ALL_ROUTES) {
      await page.goto(route, { timeout: 15000 });
      await expect(page.locator('#root'), `#root should mount on ${route}`).toBeAttached();
    }
    expect(notFound).toEqual([]);
  });

  test('Dashboard KPIs render', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('kpi-server')).toBeVisible();
    await expect(page.getByTestId('kpi-tools')).toBeVisible();
    await expect(page.getByTestId('backend-dot')).toBeVisible();
  });

  test('Bookmarks page renders and loads', async ({ page }) => {
    await page.goto('/bookmarks');
    await expect(page.getByTestId('bookmarks-page')).toBeAttached();
    await expect(page.getByTestId('bookmarks-browser-select')).toBeVisible();
    await expect(page.getByTestId('bookmarks-source-count')).toBeVisible();
    // Page auto-loads; accept list items, an empty state, a no-source warning, or an error.
    await expect(page.getByTestId('bookmarks-list-button')).toBeEnabled({ timeout: 30000 });
    const outcomes = [
      await page.getByTestId('bookmarks-item').count(),
      await page.getByTestId('bookmarks-no-source-warning').count(),
      await page.locator('[data-testid="bookmarks-page"] .bg-red-900\\/50').count(),
    ];
    expect(outcomes.reduce((a, b) => a + b, 0)).toBeGreaterThan(0);
  });

  test('Bookmarks add form opens', async ({ page }) => {
    await page.goto('/bookmarks');
    await page.getByTestId('bookmarks-add-toggle').click();
    await expect(page.getByTestId('bookmarks-add-form')).toBeVisible();
    await expect(page.getByTestId('bookmarks-add-url')).toBeVisible();
    await expect(page.getByTestId('bookmarks-add-submit')).toBeDisabled();
    await page.getByTestId('bookmarks-add-url').fill('https://example.com');
    await expect(page.getByTestId('bookmarks-add-submit')).toBeEnabled();
  });

  test('Bookmarks drilldown opens and shows details', async ({ page }) => {
    await page.goto('/bookmarks');
    await page.getByTestId('bookmarks-list-button').click();
    await expect(page.getByTestId('bookmark-open-detail').first()).toBeVisible({ timeout: 30000 });
    await page.getByTestId('bookmark-open-detail').first().click();
    await expect(page.getByTestId('bookmark-detail')).toBeVisible();
    await expect(page.getByTestId('bookmark-detail-age')).toBeVisible();
    await page.getByTestId('bookmark-detail-close').click();
    await expect(page.getByTestId('bookmark-detail')).toHaveCount(0);
  });

  test('Bookmarks pagination controls render', async ({ page }) => {
    await page.goto('/bookmarks');
    await page.getByTestId('bookmarks-list-button').click();
    await expect(page.getByTestId('bookmarks-prev')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('bookmarks-next')).toBeVisible();
    await expect(page.getByTestId('bookmarks-page-size')).toBeVisible();
    await expect(page.getByTestId('bookmarks-sort')).toBeVisible();
    await expect(page.getByTestId('bookmarks-folder-filter')).toBeVisible();
    await expect(page.getByTestId('bookmarks-tag-filter')).toBeVisible();
  });
});
