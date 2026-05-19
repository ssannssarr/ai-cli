#!/usr/bin/env node

import { spawn } from "child_process";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

const pythonCommand = process.platform === "win32" ? "python" : "python3";

const child = spawn(pythonCommand, ["main.py"], {
  cwd: root,
  stdio: "inherit"
});

child.on("error", (error) => {
  console.error(`Failed to start Python: ${error.message}`);
  console.error("Make sure Python 3 is installed and available in your PATH.");
  process.exit(1);
});

child.on("close", (code) => {
  process.exit(code ?? 0);
});
