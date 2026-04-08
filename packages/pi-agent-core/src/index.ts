import type {
  AiProvider,
  CompletionMessage
} from "@cyber-persona/pi-ai";

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

// ============ Orchestrator Types ============

export interface ExecutionPlan {
  reasoning: string;
  steps: ExecutionStep[];
}

export type ExecutionStep =
  | { type: 'announce'; text: string }
  | {
    type: 'persona';
    personaId: string;
    dependsOn: string[];  // 依赖的其他 personaId
  };

export interface ExecutionResult {
  step: ExecutionStep;
  output: string;
  sharedData?: Record<string, unknown>;
}

// ============ Orchestrator Implementation ============

export class Orchestrator {
  constructor(
    private provider: AiProvider,
    private personas: Array<{ id: string; displayName: string; introduction?: string; skills?: string[] }>
  ) { }

  /**
   * LLM 分析用户需求，决定需要哪些 persona 参与
   */
  async createPlan(userMessage: string): Promise<ExecutionPlan> {
    const personaDescriptions = this.personas.map(p =>
      `- ${p.id} (${p.displayName}): ${p.introduction || ''} [skills: ${(p.skills || []).join(', ')}]`
    ).join('\n');

    const response = await this.provider.complete({
      messages: [
        {
          role: "system",
          content: `你是调度中心，负责分析用户需求并决定需要哪些 persona 参与。

可用 persona：
${personaDescriptions}

你必须返回 JSON 格式的执行计划：
{
  "reasoning": "分析为什么需要这些 persona",
  "steps": [
    { "type": "announce", "text": "开场白，告诉用户你安排了谁" },
    { "type": "persona", "personaId": "researcher", "dependsOn": [] },
    { "type": "persona", "personaId": "critic", "dependsOn": ["researcher"] }
  ]
}

规则：
1. 第一个 step 必须是 announce（调度中心的开场白）
2. dependsOn 表示该 persona 需要等待哪些 persona 完成才能执行
3. 如果 personas 之间没有依赖，可以并行执行`
        },
        {
          role: "user",
          content: userMessage
        }
      ],
      temperature: 1,
      maxTokens: 1000
    });

    return this.parsePlan(response.text);
  }

  private parsePlan(text: string): ExecutionPlan {
    try {
      // 尝试提取 JSON
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]) as ExecutionPlan;
      }
    } catch {
      console.warn('Failed to parse plan JSON, using fallback');
    }

    // Fallback：只使用第一个 persona
    return {
      reasoning: 'Fallback: using default persona',
      steps: [
        { type: 'announce', text: '我来帮你看看这个问题。' },
        { type: 'persona', personaId: this.personas[0]?.id || 'bowie', dependsOn: [] }
      ]
    };
  }
}

// ============ Skill Registry ============

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

  /**
   * 使用 LLM 选择最适合的 skills
   */
  public async selectSkillsWithLLM(
    task: AgentTask,
    provider: AiProvider
  ): Promise<string[]> {
    const availableSkills = this.list();

    if (availableSkills.length === 0) {
      return [];
    }

    const skillDescriptions = availableSkills
      .map(s => `- ${s.name}: ${s.description}`)
      .join('\n');

    try {
      const response = await provider.complete({
        messages: [
          {
            role: "system",
            content: `你是 skill 选择器。根据用户的 goal，选择最合适的 skills。

可用 skills：
${skillDescriptions}

返回 JSON 数组格式：["skill1", "skill2"] 或者 []`
          },
          {
            role: "user",
            content: `Goal: ${task.goal}\n\nConstraints: ${task.constraints?.join('; ') || 'None'}`
          }
        ],
        temperature: 1,
        maxTokens: 500
      });

      const text = response.text.trim();
      const jsonMatch = text.match(/\[[\s\S]*\]/);
      const jsonText = jsonMatch ? jsonMatch[0] : text;
      const selectedSkills = JSON.parse(jsonText) as string[];

      if (Array.isArray(selectedSkills)) {
        const validSkills = availableSkills.map(s => s.name);
        return selectedSkills.filter(name => validSkills.includes(name));
      }
    } catch (error) {
      console.warn('LLM skill selection failed:', error);
    }

    // Fallback: 使用关键词匹配
    return this.selectSkillsByKeywords(task);
  }

  private selectSkillsByKeywords(task: AgentTask): string[] {
    const normalizedGoal = task.goal.toLowerCase();
    const matched: string[] = [];

    for (const skill of this.list()) {
      if (skill.triggers?.some(trigger => normalizedGoal.includes(trigger.toLowerCase()))) {
        matched.push(skill.name);
      }
    }

    return [...new Set(matched)];
  }
}

// ============ Agent Session ============

export interface AgentResult {
  summary: string;
  steps: string[];
  raw: string;
  soul?: string;
  skillResults: SkillResult[];
}

export class AgentSession {
  private readonly transcript: CompletionMessage[] = [];
  private readonly skillRegistry = new SkillRegistry();
  private soulText?: string;
  private sharedContext: Record<string, unknown> = {};

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

  public setSharedContext(context: Record<string, unknown>): void {
    this.sharedContext = { ...this.sharedContext, ...context };
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

  /**
   * 运行任务：内部选择 skills，生成回复
   */
  public async run(task: AgentTask): Promise<AgentResult> {
    // 1. 选择并执行 skills
    const skillNames = await this.skillRegistry.selectSkillsWithLLM(task, this.provider);
    const skillResults: SkillResult[] = [];

    for (const skillName of skillNames) {
      const skill = this.skillRegistry.get(skillName);
      if (skill) {
        const result = await skill.execute(task);
        skillResults.push(result);
      }
    }

    // 2. 构建 prompt（包含 skill 结果和共享上下文）
    const prompt = this.buildPrompt(task, skillResults);
    this.transcript.push({
      role: "user",
      content: prompt
    });

    // 3. 生成回复
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

    // 添加共享上下文（其他 persona 的结果）
    const sharedEntries = Object.entries(this.sharedContext);
    if (sharedEntries.length > 0) {
      lines.push('Shared Context:');
      for (const [key, value] of sharedEntries) {
        lines.push(`- ${key}: ${JSON.stringify(value)}`);
      }
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

export async function loadSoulFile(path: string): Promise<string> {
  const { readFile } = await import("node:fs/promises");
  return readFile(path, "utf8");
}

export function createDefaultSystemPrompt(): string {
  return [
    "You are a practical coding agent.",
    "Reason in steps, stay concise, and propose changes that are easy to maintain.",
    "If a SOUL file is provided, align your tone and behavior with it.",
    "If skills are provided, incorporate their outputs into the plan."
  ].join(" ");
}
