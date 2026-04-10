import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class ReportsPage extends BasePage {
  readonly header: Locator;
  readonly reportsCard: Locator;
  readonly reportsList: Locator;

  constructor(page: Page) {
    super(page);
    this.header = page.getByTestId('reports-header');
    this.reportsCard = page.getByTestId('reports-card');
    this.reportsList = page.getByTestId('reports-list');
  }

  async getReportCount(): Promise<number> {
    const reportElements = await this.page.getByTestId(/report-item-/).all();
    return reportElements.length;
  }

  async getReportTitles(): Promise<string[]> {
    const reportElements = await this.page.getByTestId(/report-title-/).all();
    return Promise.all(reportElements.map(async el => el.innerText()));
  }
}
