import type {
  AiProvider,
  CompletionChunk,
  CompletionMessage
} from "@cyber-bowie/pi-ai";
import { readFile } from "node:fs/promises";

export interface AgentTask {
  goal: string;
  constraints?: string[];
  context?: string[];
}

export interface SkillMetadata {
  name: string;
  description: string;
  triggers?: string[];
  version?: string;
  requiredTools?: string[];
}

export interface SkillResult {
  skillName: string;
  summary: string;
  details: string[];
  data?: unknown;
}

export interface AgentSkill {
  readonly metadata: SkillMetadata;
  execute(task: AgentTask): Promise<SkillResult>;
}

export interface AgentResult {
  summary: string;
  steps: string[];
  raw: string;
  soul?: string;
  skillResults: SkillResult[];
}

export class SkillRegistry {
  private readonly skills = new Map<string, AgentSkill>();

  public register(skill: AgentSkill): void {
    this.skills.set(skill.metadata.name, skill);
  }

  public registerMany(skills: AgentSkill[]): void {
    for (const skill of skills) {
      this.register(skill);
    }
  }

  public get(name: string): AgentSkill | undefined {
    return this.skills.get(name);
  }

  public list(): SkillMetadata[] {
    return [...this.skills.values()].map((skill) => skill.metadata);
  }
}

export async function loadSoulFile(path: string): Promise<string> {
  return readFile(path, "utf8");
}

export class AgentSession {
  private readonly transcript: CompletionMessage[] = [];
  private readonly skillRegistry = new SkillRegistry();
  private soulText?: string;

  public constructor(
    private readonly provider: AiProvider,
    private readonly systemPrompt: string
  ) {
    this.transcript.push({
      role: "system",
      content: systemPrompt
    });
  }

  public setSoul(soulText: string): void {
    this.soulText = soulText.trim();
  }

  public registerSkill(skill: AgentSkill): void {
    this.skillRegistry.register(skill);
  }

  public registerSkills(skills: AgentSkill[]): void {
    this.skillRegistry.registerMany(skills);
  }

  public listSkills(): SkillMetadata[] {
    return this.skillRegistry.list();
  }

  public async run(task: AgentTask): Promise<AgentResult> {
    const skillResults = await this.runTriggeredSkills(task);
    const prompt = this.buildPrompt(task, skillResults);
    this.transcript.push({
      role: "user",
      content: prompt
    });

    const response = await this.provider.complete({
      messages: this.transcript,
      temperature: 1
    });

    this.transcript.push({
      role: "assistant",
      content: response.text
    });

    return {
      summary: this.extractSummary(response.text),
      steps: this.extractSteps(response.text),
      raw: response.text,
      soul: this.soulText,
      skillResults
    };
  }

  public async *runStream(task: AgentTask): AsyncIterable<{
    chunk: CompletionChunk;
    aggregateText: string;
    skillResults: SkillResult[];
    soul?: string;
  }> {
    if (!this.provider.streamComplete) {
      const result = await this.run(task);
      yield {
        chunk: {
          textDelta: result.raw
        },
        aggregateText: result.raw,
        skillResults: result.skillResults,
        soul: result.soul
      };
      return;
    }

    const skillResults = await this.runTriggeredSkills(task);
    const prompt = this.buildPrompt(task, skillResults);
    this.transcript.push({
      role: "user",
      content: prompt
    });

    let aggregateText = "";

    for await (const chunk of this.provider.streamComplete({
      messages: this.transcript,
      temperature: 0.2
    })) {
      aggregateText += chunk.textDelta;
      yield {
        chunk,
        aggregateText,
        skillResults,
        soul: this.soulText
      };
    }

    this.transcript.push({
      role: "assistant",
      content: aggregateText
    });
  }

  private async runTriggeredSkills(task: AgentTask): Promise<SkillResult[]> {
    const normalizedGoal = task.goal.toLowerCase();

    const matchedSkills = this.skillRegistry
      .list()
      .filter((skill) =>
        skill.triggers?.some((trigger) => normalizedGoal.includes(trigger.toLowerCase()))
      )
      .map((skill) => this.skillRegistry.get(skill.name))
      .filter((skill): skill is AgentSkill => Boolean(skill));

    const uniqueSkills = new Map<string, AgentSkill>();

    for (const skill of matchedSkills) {
      uniqueSkills.set(skill.metadata.name, skill);
    }

    const results: SkillResult[] = [];

    for (const skill of uniqueSkills.values()) {
      results.push(await skill.execute(task));
    }

    return results;
  }

  private buildPrompt(task: AgentTask, skillResults: SkillResult[]): string {
    const lines = [`Goal: ${task.goal}`];

    if (task.constraints?.length) {
      lines.push(`Constraints: ${task.constraints.join("; ")}`);
    }

    if (task.context?.length) {
      lines.push(`Context: ${task.context.join("; ")}`);
    }

    if (this.soulText) {
      lines.push(`Soul:\n${this.soulText}`);
    }

    if (skillResults.length > 0) {
      lines.push(
        `Skill Results:\n${skillResults
          .map(
            (result) =>
              `- ${result.skillName}: ${result.summary}\n${result.details
                .map((detail) => `  * ${detail}`)
                .join("\n")}`
          )
          .join("\n")}`
      );
    }

    return lines.join("\n");
  }

  private extractSummary(text: string): string {
    const firstContentLine = text
      .split("\n")
      .find((line) => line.trim().length > 0 && !line.startsWith("Plan:"));

    return firstContentLine ?? "No summary generated.";
  }

  private extractSteps(text: string): string[] {
    return text
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => /^\d+\./.test(line));
  }
}

export function createDefaultSystemPrompt(): string {
  return [
    "You are a practical coding agent.",
    "Reason in steps, stay concise, and propose changes that are easy to maintain.",
    "If a SOUL file is provided, align your tone and behavior with it.",
    "If skills are provided, incorporate their outputs into the plan."
  ].join(" ");
}
