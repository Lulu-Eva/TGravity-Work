#!/usr/bin/env node

import { copyFileSync, cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const __dirname = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(__dirname, "..");
const skillName = "tgravity-work";

const targets = {
  codex: [
    join(homedir(), ".agents", "skills", skillName),
    join(homedir(), ".codex", "skills", skillName),
  ],
  "codex-agents": [join(homedir(), ".agents", "skills", skillName)],
  "codex-legacy": [join(homedir(), ".codex", "skills", skillName)],
  claude: [join(homedir(), ".claude", "skills", skillName)],
  codebuddy: [join(homedir(), ".codebuddy", "skills", skillName)],
  workbuddy: [join(homedir(), ".workbuddy", "skills", skillName)],
};

const includeEntries = [
  "SKILL.md",
  "agents",
  "assets",
  "references",
  "scripts",
];

function usage() {
  console.log(`TGravity Work Skill installer

Usage:
  npx tgravity-work
  npx tgravity-work --target codex
  npx tgravity-work --target all
  npx tgravity-work --dest ~/.agents/skills/tgravity-work

Options:
  --target <target>  Install target: codex, codex-agents, codex-legacy,
                     claude, codebuddy, workbuddy, all
                     Default: codex
  --dest <path>      Custom install directory
  --force            Replace existing install directory
  --help             Show this help
`);
}

function parseArgs(argv) {
  const args = {
    target: "codex",
    dest: "",
    force: false,
    help: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--force") {
      args.force = true;
    } else if (arg === "--target") {
      args.target = argv[++i] || "";
    } else if (arg.startsWith("--target=")) {
      args.target = arg.slice("--target=".length);
    } else if (arg === "--dest") {
      args.dest = argv[++i] || "";
    } else if (arg.startsWith("--dest=")) {
      args.dest = arg.slice("--dest=".length);
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }

  return args;
}

function expandHome(path) {
  if (path === "~") return homedir();
  if (path.startsWith("~/")) return join(homedir(), path.slice(2));
  return path;
}

function normalizeDest(dest) {
  return resolve(expandHome(dest));
}

function uniqueDests(dests) {
  return [...new Set(dests.map((dest) => normalizeDest(dest)))];
}

function copyEntry(entry, destRoot) {
  const source = join(packageRoot, entry);
  const dest = join(destRoot, entry);
  if (!existsSync(source)) return;
  mkdirSync(dirname(dest), { recursive: true });
  if (entry.endsWith(".md")) {
    copyFileSync(source, dest);
  } else {
    cpSync(source, dest, { recursive: true });
  }
}

function assertCanInstall(dests, force) {
  if (force) return;
  const existing = dests.filter((dest) => existsSync(dest));
  if (existing.length > 0) {
    throw new Error(
      `Install directory already exists:\n${existing.map((dest) => `- ${dest}`).join("\n")}\nRe-run with --force to replace it.`,
    );
  }
}

function installTo(installDir, force) {
  if (existsSync(installDir) && force) {
    rmSync(installDir, { recursive: true, force: true });
  }

  mkdirSync(installDir, { recursive: true });
  for (const entry of includeEntries) {
    copyEntry(entry, installDir);
  }
  console.log(`Installed ${skillName} to ${installDir}`);
}

function resolveDestinations(args) {
  if (args.dest) return uniqueDests([args.dest]);
  if (args.target === "all") {
    return uniqueDests([
      ...targets.codex,
      ...targets.claude,
      ...targets.codebuddy,
      ...targets.workbuddy,
    ]);
  }
  if (!targets[args.target]) {
    throw new Error(
      `Invalid target: ${args.target}. Expected codex, codex-agents, codex-legacy, claude, codebuddy, workbuddy, or all.`,
    );
  }
  return uniqueDests(targets[args.target]);
}

try {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    process.exit(0);
  }

  const destinations = resolveDestinations(args);
  assertCanInstall(destinations, args.force);

  for (const dest of destinations) {
    installTo(dest, args.force);
  }

  console.log("Restart your agent app to load the skill.");
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
