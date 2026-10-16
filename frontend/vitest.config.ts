import { defineConfig } from "vitest/config";
export default defineConfig({
  define: { "import.meta.env.VITE_MODE": JSON.stringify("showcase") },
  test: { include: ["src/**/*.test.ts"] },
});
