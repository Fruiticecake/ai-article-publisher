import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  readonly statsCards: Locator;
  readonly totalProjectsCard: Locator;
  readonly totalReportsCard: Locator;
  readonly avgStarsCard: Locator;
  readonly systemStatusCard: Locator;
  readonly recentProjectsCard: Locator;
  readonly recentReportsCard: Locator;
  readonly totalProjects: Locator;
  readonly totalReports: Locator;
  readonly avgStars: Locator;
  readonly systemStatus: Locator;

  constructor(page: Page) {
    super(page);
    this.statsCards = page.getByTestId('stats-cards');
    this.totalProjectsCard = page.getByTestId('total-projects-card');
    this.totalReportsCard = page.getByTestId('total-reports-card');
    this.avgStarsCard = page.getByTestId('avg-stars-card');
    this.systemStatusCard = page.getByTestId('system-status-card');
    this.recentProjectsCard = page.getByTestId('recent-projects-card');
    this.recentReportsCard = page.getByTestId('recent-reports-card');
    this.totalProjects = page.getByTestId('total-projects');
    this.totalReports = page.getByTestId('total-reports');
    this.avgStars = page.getByTestId('avg-stars');
    this.systemStatus = page.getByTestId('system-status');
  }

  async getTotalProjects(): Promise<string> {
    return this.getElementText(this.totalProjects);
  }

  async getTotalReports(): Promise<string> {
    return this.getElementText(this.totalReports);
  }

  async getAvgStars(): Promise<string> {
    return this.getElementText(this.avgStars);
  }

  async getSystemStatus(): Promise<string> {
    return this.getElementText(this.systemStatus);
  }
}
