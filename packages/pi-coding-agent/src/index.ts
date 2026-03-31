#!/usr/bin/env node

import { resolve } from "node:path";
import { MockProvider } from "@cyber-bowie/pi-ai";
import {
  AgentSession,
  createDefaultSystemPrompt,
  loadSoulFile
} from "@cyber-bowie/pi-agent-core";
import { superpowerSkill } from "@cyber-bowie/pi-skills-superpower";

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

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));

  const session = new AgentSession(
    new MockProvider("pi-coding-agent-mock"),
    createDefaultSystemPrompt()
  );

  session.registerSkill(superpowerSkill);
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
