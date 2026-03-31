#!/usr/bin/env node

import { resolve } from "node:path";
import { config as loadEnv } from "dotenv";
import { OpenAiProvider } from "@cyber-bowie/pi-ai";
import {
  AgentSession,
  createDefaultSystemPrompt,
  loadSoulFile
} from "@cyber-bowie/pi-agent-core";
import {
  createCyberBowieSearchSkill,
  createMcpSearchRuntime
} from "@cyber-bowie/pi-skills-search";
import { superpowerSkill } from "@cyber-bowie/pi-skills-superpower";

loadEnv({
  path: resolve(process.cwd(), ".env"),
  override: true
});

interface CliOptions {
  goal?: string;
  enabledSkills: string[];
  listSkills: boolean;
}

function parseArgs(argv: string[]): CliOptions {
  const enabledSkills: string[] = [];
  const goalParts: string[] = [];
  let listSkills = false;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--skill") {
      const skillName = argv[index + 1];

      if (skillName) {
        enabledSkills.push(skillName);
        index += 1;
      }

      continue;
    }

    if (arg === "--list-skills") {
      listSkills = true;
      continue;
    }

    goalParts.push(arg);
  }

  return {
    goal: goalParts.join(" ").trim() || undefined,
    enabledSkills,
    listSkills
  };
}

function getRequiredEnv(name: string): string {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(`缺少环境变量 ${name}，请先配置 .env`);
  }

  return value;
}

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));

  const session = new AgentSession(
    new OpenAiProvider({
      apiKey: getRequiredEnv("OPENAI_API_KEY"),
      model: process.env.OPENAI_MODEL?.trim() || "gpt-4.1-mini",
      baseUrl: process.env.OPENAI_BASE_URL?.trim() || undefined,
      temperature: process.env.OPENAI_TEMPERATURE
        ? Number(process.env.OPENAI_TEMPERATURE)
        : 0.4
    }),
    createDefaultSystemPrompt()
  );

  session.registerSkill(superpowerSkill);
  if (process.env.MCP_SEARCH_URL?.trim()) {
    session.registerSkill(
      createCyberBowieSearchSkill(
        createMcpSearchRuntime({
          serverUrl: process.env.MCP_SEARCH_URL.trim(),
          toolName: process.env.MCP_SEARCH_TOOL?.trim() || "bailian_web_search",
          authToken: process.env.MCP_SEARCH_AUTH_TOKEN?.trim() || undefined,
          authHeader: process.env.MCP_SEARCH_AUTH_HEADER?.trim() || undefined,
          resultCount: process.env.MCP_SEARCH_RESULT_COUNT
            ? Number(process.env.MCP_SEARCH_RESULT_COUNT)
            : 10
        })
      )
    );
  }
  session.setSoul(await loadSoulFile(resolve(process.cwd(), "SOUL.md")));

  if (options.listSkills) {
    const content = session
      .listSkills()
      .map((skill) => `${skill.name}: ${skill.description}`)
      .join("\n");

    process.stdout.write(`${content}\n`);
    return;
  }

  if (!options.goal) {
    process.stderr.write(
      "Usage: pi-coding-agent [--list-skills] [--skill superpower] \"describe the coding task you want help with\"\n"
    );
    process.exitCode = 1;
    return;
  }

  const inferredGoal =
    options.enabledSkills.length > 0
      ? `${options.enabledSkills.join(" ")} ${options.goal}`
      : options.goal;

  const result = await session.run({
    goal: inferredGoal,
    constraints: [
      "Prefer TypeScript",
      "Keep the implementation small and composable"
    ],
    context: [
      "This repository is a personal project inspired by pi-mono",
      "The assistant persona is defined in SOUL.md",
      "Skills can enrich the plan before the model responds"
    ]
  });

  const sections = [result.raw];

  if (result.skillResults.length > 0) {
    sections.push(
      [
        "Activated Skills:",
        ...result.skillResults.map(
          (skill) => `- ${skill.skillName}: ${skill.summary}`
        )
      ].join("\n")
    );
  }

  process.stdout.write(`${sections.join("\n\n")}\n`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`pi-coding-agent failed: ${message}\n`);
  process.exitCode = 1;
});
