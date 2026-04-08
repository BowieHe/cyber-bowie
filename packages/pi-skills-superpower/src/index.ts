import type { AgentSkill, AgentTask, SkillResult } from "@cyber-persona/pi-agent-core";

export class SuperpowerSkill implements AgentSkill {
  public readonly metadata = {
    name: "superpower",
    description:
      "Turns a raw request into a stronger execution angle with leverage, structure, and concrete next moves.",
    triggers: ["superpower", "增强", "强化", "升级", "突破"]
  };

  public async execute(task: AgentTask): Promise<SkillResult> {
    const boosts = [
      "Reframe the task around the user's real outcome instead of the first implementation detail.",
      "Split the work into a minimal usable version and a clear upgrade path.",
      "Call out one leverage point that can make the project feel more personal or differentiated."
    ];

    const notes = [
      `Primary goal: ${task.goal}`,
      "Minimal version: build the smallest flow that is already useful.",
      "Upgrade path: add model integrations, richer tools, and more skills after the base loop works.",
      "Differentiator: keep the agent's tone and workflow personal through SOUL-driven behavior."
    ];

    return {
      skillName: this.metadata.name,
      summary: "Applied superpower framing to make the plan more intentional and more leverage-driven.",
      details: [...boosts, ...notes]
    };
  }
}

export const superpowerSkill = new SuperpowerSkill();
