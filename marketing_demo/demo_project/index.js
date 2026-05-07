import { DashboardController } from './ui.js';

export function bootstrapApplication() {
  const dashboard = new DashboardController();
  return dashboard.initialize();
}

bootstrapApplication();
