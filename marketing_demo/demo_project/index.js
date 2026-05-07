import { DashboardController } from './ui.js';

export async function bootstrapApplication() {
  const dash = new DashboardController();
  return dash.loadPrimaryUser();
}

bootstrapApplication();
