import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: { outDir: "dist", emptyOutDir: true },
  server: { proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true, rewrite: path => path.replace(/^\/api/, "") } } },
  test: { environment: "jsdom", setupFiles: "./src/test-setup.ts", globals: true },
});
