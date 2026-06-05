import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ["nutrient-stem-untruth.ngrok-free.dev"],
  },
  test: {
    environment: "node",
    globals: true,
  },
});
