# cyber-bowie

A personal TypeScript monorepo inspired by `pi-mono`, with a local `SOUL.md` persona file and a pluggable skill system.

## Packages

- `@cyber-bowie/pi-ai`: lightweight model/provider abstractions
- `@cyber-bowie/pi-agent-core`: reusable agent runtime, soul loading, and skill registry
- `@cyber-bowie/pi-coding-agent`: CLI coding assistant
- `@cyber-bowie/pi-skills-superpower`: first built-in skill package
- `@cyber-bowie/pi-web-chat`: local React + TypeScript web UI with a ChatGPT-like layout

## Getting started

```bash
npm install
npm run build
npm run agent -- --list-skills
npm run agent -- --skill superpower "帮我设计一个个人项目结构"
npm run web
```

Then open `http://localhost:3000`.

## Soul

The root [SOUL.md](/home/bowie/code/cyber-bowie/SOUL.md) file defines the assistant's personality, tone, working style, and guardrails.

## Skills

- Skills can be registered into the agent runtime.
- `superpower` is enabled by default in the CLI.
- More skills can be ported later using the same interface.

## Web UI

- ChatGPT-like sidebar + conversation layout
- Local Node server with `/api/chat` and `/api/skills`
- Frontend implemented with React + TypeScript
- Uses `SOUL.md` and the built-in `superpower` skill

## Notes

- This is a clean-room personal implementation inspired by the structure of `pi-mono`.
- `.codex` and `codex` are ignored via `.gitignore`.
