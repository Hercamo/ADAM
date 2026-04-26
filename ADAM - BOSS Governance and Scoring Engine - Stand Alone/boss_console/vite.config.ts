import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// BOSS Console — Vite config.
// The backend URL is configurable via the BOSS_API_URL env var so the
// same built bundle can be deployed against any BOSS Engine instance.
// In development, Vite's proxy routes /v1/* to localhost:8080 so the
// UI and API share an origin and avoid CORS friction.

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    proxy: {
      "/v1": {
        target: process.env.BOSS_API_URL ?? "http://localhost:8080",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    port: 5173,
    host: "0.0.0.0",
  },
  build: {
    outDir: "dist",
    sourcemap: mode !== "production",
    target: "es2020",
    rollupOptions: {
      output: {
        manualChunks: {
          recharts: ["recharts"],
          react: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
}));
