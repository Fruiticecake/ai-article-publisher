import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class SettingsPage extends BasePage {
  readonly header: Locator;
  readonly saveAllButton: Locator;
  readonly githubConfigCard: Locator;
  readonly githubTokenInput: Locator;

  constructor(page: Page) {
    super(page);
    this.header = page.getByTestId('settings-header');
    this.saveAllButton = page.getByTestId('save-all-button');
    this.githubConfigCard = page.getByTestId('github-config-card');
    this.githubTokenInput = page.getByTestId('github-token-input');
  }

  async setGithubToken(token: string) {
    await this.fillInput(this.githubTokenInput, token);
  }

  async saveAllSettings() {
    await this.clickElement(this.saveAllButton);
  }

  async isGithubConfigVisible(): Promise<boolean> {
    return this.isElementVisible(this.githubConfigCard);
  }
}
