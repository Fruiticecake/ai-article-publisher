# E2E Tests for Auto Publisher

This directory contains end-to-end (E2E) tests for the Auto Publisher application using Playwright.

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Install Playwright browsers:

```bash
npx playwright install
```

## Running Tests

### All Tests

```bash
npm run test:e2e
```

### In Headed Mode (Watch the browser)

```bash
npm run test:e2e:headed
```

### With UI Mode

```bash
npm run test:e2e:ui
```

### Debug Mode

```bash
npm run test:e2e:debug
```

### Specific Test File

```bash
npx playwright test tests/e2e/auth.spec.ts
```

### Specific Browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Viewing Reports

```bash
npm run test:e2e:report
```

## Project Structure

```
tests/e2e/
├── pages/              # Page Object Models
│   ├── BasePage.ts     # Base page with common methods
│   ├── LoginPage.ts
│   ├── DashboardPage.ts
│   ├── ProjectsPage.ts
│   ├── ReportsPage.ts
│   ├── PublishPage.ts
│   ├── SettingsPage.ts
│   └── index.ts
├── auth.spec.ts        # Authentication tests
├── dashboard.spec.ts   # Dashboard tests
├── projects.spec.ts    # Projects page tests
├── reports.spec.ts     # Reports page tests
├── publish.spec.ts     # Publish page tests
├── settings.spec.ts    # Settings page tests
└── README.md           # This file
```

## Test Credentials

The tests use the following default credentials:

- Username: `admin`
- Password: `admin123`

Make sure the backend server is running with these credentials configured.

## Configuration

The Playwright configuration is in `playwright.config.ts` in the frontend directory.

Key configuration:

- Base URL: `http://localhost:8080`
- Test directory: `tests/e2e`
- Browsers: Chromium, Firefox, WebKit
- Traces: Enabled on first retry
- Screenshots: Taken on failure
- Videos: Retained on failure

## Data-Testid Attributes

The tests use `data-testid` attributes for stable selectors. These attributes are added to key elements in the frontend components.

## CI/CD

For CI environments, the configuration automatically:

- Uses 2 retries
- Runs with 1 worker
- Generates JUnit XML report
