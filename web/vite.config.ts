import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  build: {
    outDir: "../api/app/static",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(import.meta.dirname, "src/main.ts"),
      output: {
        entryFileNames: "main.js",
        assetFileNames: "[name][extname]",
      },
    },
  },
});
