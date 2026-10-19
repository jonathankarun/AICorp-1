// this file configures the local web build
// it forwards API requests to the backend during development
import { defineConfig } from "vite";
export default defineConfig({
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
