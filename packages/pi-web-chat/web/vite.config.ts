import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const configDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: configDir,
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1"
  },
  build: {
    outDir: resolve(configDir, "dist"),
    emptyOutDir: true
  }
});
