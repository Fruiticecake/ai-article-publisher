import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class PublishPage extends BasePage {
  readonly publishGrid: Locator;
  readonly scheduleConfigCard: Locator;
  readonly manualPublishCard: Locator;
  readonly documentExportCard: Locator;
  readonly reportPublishCard: Locator;
  readonly platformsStatusCard: Locator;
  readonly scheduleToggle: Locator;
  readonly cronInput: Locator;
  readonly timezoneSelect: Locator;
  readonly saveScheduleButton: Locator;
  readonly platformsGrid: Locator;
  readonly triggerPublishButton: Locator;
  readonly projectSelect: Locator;
  readonly platformsStatus: Locator;

  constructor(page: Page) {
    super(page);
    this.publishGrid = page.getByTestId('publish-grid');
    this.scheduleConfigCard = page.getByTestId('schedule-config-card');
    this.manualPublishCard = page.getByTestId('manual-publish-card');
    this.documentExportCard = page.getByTestId('document-export-card');
    this.reportPublishCard = page.getByTestId('report-publish-card');
    this.platformsStatusCard = page.getByTestId('platforms-status-card');
    this.scheduleToggle = page.getByTestId('schedule-toggle');
    this.cronInput = page.getByTestId('cron-input');
    this.timezoneSelect = page.getByTestId('timezone-select');
    this.saveScheduleButton = page.getByTestId('save-schedule-button');
    this.platformsGrid = page.getByTestId('platforms-grid');
    this.triggerPublishButton = page.getByTestId('trigger-publish-button');
    this.projectSelect = page.getByTestId('project-select');
    this.platformsStatus = page.getByTestId('platforms-status');
  }

  async toggleSchedule() {
    await this.clickElement(this.scheduleToggle);
  }

  async setCronExpression(cron: string) {
    await this.fillInput(this.cronInput, cron);
  }

  async selectTimezone(timezone: string) {
    await this.page.selectOption(this.timezoneSelect, timezone);
  }

  async saveSchedule() {
    await this.clickElement(this.saveScheduleButton);
  }

  async selectPlatform(platform: string) {
    const platformButton = this.page.getByTestId(`platform-button-${platform}`);
    await this.clickElement(platformButton);
  }

  async triggerPublish() {
    await this.clickElement(this.triggerPublishButton);
  }

  async selectProject(projectId: string) {
    await this.page.selectOption(this.projectSelect, projectId);
  }

  async getEnabledPlatformCount(): Promise<number> {
    const enabledPlatforms = await this.platformsStatus
      .getByTestId(/platform-status-/)
      .filter({ hasText: '已启用' })
      .all();
    return enabledPlatforms.length;
  }
}
