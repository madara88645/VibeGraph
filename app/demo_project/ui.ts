export type PlanStep = {
  order: number;
  topic: string;
  minutes: number;
  risk: string;
};

export class ThemeController {
  private mode = "focus";

  setMode(mode: string) {
    this.mode = mode;
    return this.mode;
  }
}

export const formatMinutes = (minutes: number) => `${minutes} min`;

export function renderPlan(steps: PlanStep[]) {
  return steps.map((step) => `${step.order}. ${step.topic} - ${formatMinutes(step.minutes)}`);
}
