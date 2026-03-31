#!/usr/bin/env node

import { MockProvider } from "@cyber-bowie/pi-ai";
import {
  AgentSession,
  createDefaultSystemPrompt
} from "@cyber-bowie/pi-agent-core";

async function main(): Promise<void> {
  const goal = process.argv.slice(2).join(" ").trim();

  if (!goal) {
    process.stderr.write(
      "Usage: pi-coding-agent \"describe the coding task you want help with\"\n"
    );
    process.exitCode = 1;
    return;
  }

  const session = new AgentSession(
    new MockProvider("pi-coding-agent-mock"),
    createDefaultSystemPrompt()
  );

  const result = await session.run({
    goal,
    constraints: [
      "Prefer TypeScript",
      "Keep the implementation small and composable"
    ],
    context: [
      "This repository is a personal project inspired by pi-mono"
    ]
  });

  process.stdout.write(`${result.raw}\n`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`pi-coding-agent failed: ${message}\n`);
  process.exitCode = 1;
});
