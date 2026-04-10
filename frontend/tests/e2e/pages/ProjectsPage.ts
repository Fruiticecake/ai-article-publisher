import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class ProjectsPage extends BasePage {
  readonly header: Locator;
  readonly searchInput: Locator;
  readonly filterButton: Locator;
  readonly projectsCard: Locator;
  readonly projectsList: Locator;

  constructor(page: Page) {
    super(page);
    this.header = page.getByTestId('projects-header');
    this.searchInput = page.getByTestId('search-input');
    this.filterButton = page.getByTestId('filter-button');
    this.projectsCard = page.getByTestId('projects-card');
    this.projectsList = page.getByTestId('projects-list');
  }

  async searchProjects(query: string) {
    await this.fillInput(this.searchInput, query);
  }

  async clickFilter() {
    await this.clickElement(this.filterButton);
  }

  async getProjectNames(): Promise<string[]> {
    const projectElements = await this.page.getByTestId(/project-name-/).all();
    return Promise.all(projectElements.map(async el => el.innerText()));
  }

  async getProjectCount(): Promise<number> {
    const projectElements = await this.page.getByTestId(/project-item-/).all();
    return projectElements.length;
  }
}
