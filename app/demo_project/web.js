import { renderPlan, ThemeController } from "./ui";

export class DemoClient {
  constructor(endpoint) {
    this.endpoint = endpoint;
  }

  async fetchPlan(userId) {
    const response = await fetch(this.endpoint, {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    });
    return response.json();
  }
}

export async function bootDashboard(userId) {
  const theme = new ThemeController();
  theme.setMode("focus");
  const client = new DemoClient("/api/demo-plan");
  const plan = await client.fetchPlan(userId);
  console.log(renderPlan(plan.steps));
}
