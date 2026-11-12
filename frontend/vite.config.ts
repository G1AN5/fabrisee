import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The Django development server (API, Django admin, and their static files).
const DJANGO_URL = "http://127.0.0.1:8000";
const inCodespaces = Boolean(process.env.CODESPACES);

export default defineConfig(({ command }) => ({
  // In production Django serves the built app from /static/ (WhiteNoise).
  base: command === "build" ? "/static/" : "/",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    // Listen on all interfaces so GitHub Codespaces can forward the port.
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    allowedHosts: [".app.github.dev", "localhost", "127.0.0.1"],
    // Codespaces serves forwarded ports over HTTPS on port 443.
    hmr: inCodespaces ? { clientPort: 443 } : undefined,
    proxy: {
      "/api": DJANGO_URL,
      "/admin": DJANGO_URL,
      // Static files of the Django admin and the browsable API (/static/admin, ...).
      "/static": DJANGO_URL,
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
    restoreMocks: true,
  },
}));
