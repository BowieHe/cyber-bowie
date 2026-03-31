import type { AiProvider, CompletionMessage } from "@cyber-bowie/pi-ai";

export interface AgentTask {
  goal: string;
  constraints?: string[];
  context?: string[];
}

export interface AgentResult {
  summary: string;
  steps: string[];
  raw: string;
}

export class AgentSession {
  private readonly transcript: CompletionMessage[] = [];

  public constructor(
    private readonly provider: AiProvider,
    private readonly systemPrompt: string
  ) {
    this.transcript.push({
      role: "system",
      content: systemPrompt
    });
  }

  public async run(task: AgentTask): Promise<AgentResult> {
    const prompt = this.buildPrompt(task);
    this.transcript.push({
      role: "user",
      content: prompt
    });

    const response = await this.provider.complete({
      messages: this.transcript,
      temperature: 0.2
    });

    this.transcript.push({
      role: "assistant",
      content: response.text
    });

    return {
      summary: this.extractSummary(response.text),
      steps: this.extractSteps(response.text),
      raw: response.text
    };
  }

  private buildPrompt(task: AgentTask): string {
    const lines = [`Goal: ${task.goal}`];

    if (task.constraints?.length) {
      lines.push(`Constraints: ${task.constraints.join("; ")}`);
    }

    if (task.context?.length) {
      lines.push(`Context: ${task.context.join("; ")}`);
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
    "Reason in steps, stay concise, and propose changes that are easy to maintain."
  ].join(" ");
}
