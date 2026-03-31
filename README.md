# cyber-bowie

A personal TypeScript monorepo inspired by `pi-mono`.

## Packages

- `@cyber-bowie/pi-ai`: lightweight model/provider abstractions
- `@cyber-bowie/pi-agent-core`: reusable agent runtime and planning loop
- `@cyber-bowie/pi-coding-agent`: a small CLI coding assistant built on the core

## Getting started

```bash
npm install
npm run build
node packages/pi-coding-agent/dist/index.js "build me a small API"
```

## Notes

- This is a clean-room personal implementation inspired by the structure of `pi-mono`.
- `.codex` and `codex` are ignored via `.gitignore`.
