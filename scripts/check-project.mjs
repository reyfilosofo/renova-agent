import { existsSync } from "node:fs";

const required = [
  "README.md",
  "AGENTS.md",
  "package.json",
  "src/app/page.tsx",
  "src/app/layout.tsx",
  "src/app/globals.css",
  "src/lib/renova.ts",
  "src/lib/agent.ts",
  "src/app/api/agent/route.ts",
  "public/assets/logo-renova.svg",
  "public/assets/hero-renova.svg",
  "docs/RENOVA_AGENT_SPEC.md",
  "docs/CODEX_MOBILE_SETUP.md",
  ".github/workflows/ci.yml"
];

const missing = required.filter((path) => !existsSync(path));

if (missing.length > 0) {
  console.error("Missing required files:");
  for (const item of missing) console.error(`- ${item}`);
  process.exit(1);
}

console.log("RENOVA Agent structure check passed.");
