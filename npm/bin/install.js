#!/usr/bin/env node
/**
 * One-command installer for the BCRP toolchain.
 *
 *   npx bcrp-mcp
 *
 * Installs three things that are meant to travel together:
 *   1. the `bcrp-mcp` MCP server   (so AI clients can query BCRPData)
 *   2. the `bcrp` CLI              (same tools, for humans and scripts)
 *   3. the `bcrp` agent skill      (so agents know *how* to use them well)
 *
 * The skill without the server is advice an agent can't act on, and the server
 * without the skill gets misused (mixed frequencies, positional values), so the
 * default installs all three. Use --no-skill / --skill-only to opt out.
 *
 * Deliberately dependency-free: npx must be able to run this instantly.
 */
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const PY_PACKAGE = "bcrp-mcp";
const GIT_SPEC = "git+https://github.com/JOSETRA44/bcrp-mcp.git";
const SKILL_NAME = "bcrp";

// --- tiny output helpers ---------------------------------------------------

const COLOR =
  process.stdout.isTTY && !process.env.NO_COLOR && process.env.TERM !== "dumb";
const sgr = (code, text) => (COLOR ? `\x1b[${code}m${text}\x1b[0m` : text);
const bold = (t) => sgr("1", t);
const dim = (t) => sgr("2", t);
const green = (t) => sgr("32", t);
const yellow = (t) => sgr("33", t);
const red = (t) => sgr("31", t);

const ok = (msg) => console.log(`  ${green("✓")} ${msg}`);
const skip = (msg) => console.log(`  ${dim("·")} ${dim(msg)}`);
const warn = (msg) => console.log(`  ${yellow("!")} ${msg}`);
const fail = (msg) => console.error(`  ${red("✗")} ${msg}`);
const step = (msg) => console.log(`\n${bold(msg)}`);

// --- shell helpers ---------------------------------------------------------

function exists(cmd) {
  const probe = spawnSync(cmd, ["--version"], {
    shell: true,
    stdio: "ignore",
    windowsHide: true,
  });
  return probe.status === 0;
}

function run(cmd, args, { quiet = false } = {}) {
  const res = spawnSync(cmd, args, {
    shell: true,
    stdio: quiet ? "ignore" : "inherit",
    windowsHide: true,
  });
  return res.status === 0;
}

// --- argument parsing ------------------------------------------------------

function parseArgs(argv) {
  const opts = {
    skill: true,
    python: true,
    register: true,
    from: null,
    skillDir: null,
    help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case "-h":
      case "--help":
        opts.help = true;
        break;
      case "--skill-only":
        opts.python = false;
        opts.register = false;
        break;
      case "--no-skill":
        opts.skill = false;
        break;
      case "--no-register":
        opts.register = false;
        break;
      case "--from":
        opts.from = argv[++i];
        break;
      case "--skill-dir":
        opts.skillDir = argv[++i];
        break;
      default:
        fail(`Unknown option: ${arg}`);
        process.exit(2);
    }
  }
  return opts;
}

function printHelp() {
  console.log(`
${bold("bcrp-mcp installer")}

  Installs the BCRP MCP server, the \`bcrp\` CLI, and the \`bcrp\` agent skill.

${bold("Usage")}
  npx bcrp-mcp [options]

${bold("Options")}
  --skill-only     Install only the agent skill (no Python package).
  --no-skill       Install only the MCP server + CLI.
  --no-register    Don't register the MCP server with detected AI clients.
  --from <spec>    Install the Python package from a custom source
                   (a local path, or a git+https URL) instead of PyPI.
  --skill-dir <p>  Install the skill into <p> instead of ~/.claude/skills.
  -h, --help       Show this help.

${bold("Examples")}
  npx bcrp-mcp                      Install everything
  npx bcrp-mcp --skill-only         Just the agent skill
  npx bcrp-mcp --from .             Install the Python side from a local checkout
`);
}

// --- step 1: the Python package (MCP server + CLI) -------------------------

function pickPythonInstaller() {
  if (exists("uv")) {
    return {
      name: "uv",
      // `uv tool install` puts both console scripts on PATH in an isolated env,
      // which is what we want for a CLI + MCP server the user invokes globally.
      install: (spec, editable) =>
        run("uv", ["tool", "install", "--force", ...(editable ? ["--editable"] : []), spec]),
    };
  }
  if (exists("pipx")) {
    return {
      name: "pipx",
      install: (spec, editable) =>
        run("pipx", ["install", "--force", ...(editable ? ["--editable"] : []), spec]),
    };
  }
  for (const py of ["python3", "python", "py"]) {
    if (exists(py)) {
      return {
        name: `${py} -m pip`,
        install: (spec, editable) =>
          run(py, ["-m", "pip", "install", "--upgrade", ...(editable ? ["-e"] : []), spec]),
      };
    }
  }
  return null;
}

function installPython(opts) {
  step("Installing MCP server + CLI");

  const installer = pickPythonInstaller();
  if (!installer) {
    fail("No Python installer found (looked for uv, pipx, pip).");
    console.log(
      dim(
        "\n  Install uv — the fastest option — then re-run this command:\n" +
          "    Windows:      winget install astral-sh.uv\n" +
          "    macOS/Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh\n"
      )
    );
    return false;
  }
  skip(`using ${installer.name}`);

  // A local path is an editable dev install; anything else is a normal install.
  const isLocalPath =
    opts.from && (opts.from === "." || opts.from.startsWith("./") || fs.existsSync(opts.from));

  if (opts.from) {
    if (installer.install(opts.from, isLocalPath)) {
      ok(`Installed from ${opts.from}`);
      return true;
    }
    fail(`Could not install from ${opts.from}`);
    return false;
  }

  if (installer.install(PY_PACKAGE, false)) {
    ok(`Installed ${PY_PACKAGE}`);
    return true;
  }

  // PyPI may not have it yet (or the network blocked it) — fall back to git so
  // a fresh machine still ends up with a working install.
  warn(`PyPI install failed; falling back to ${GIT_SPEC}`);
  if (installer.install(GIT_SPEC, false)) {
    ok("Installed from GitHub");
    return true;
  }

  fail("Could not install the Python package.");
  return false;
}

// --- step 2: the agent skill ----------------------------------------------

function findBundledSkill() {
  // Packed layout: skills/ sits beside bin/. Repo layout: it's one level up.
  const candidates = [
    path.resolve(__dirname, "..", "skills", SKILL_NAME),
    path.resolve(__dirname, "..", "..", "skills", SKILL_NAME),
  ];
  return candidates.find((p) => fs.existsSync(path.join(p, "SKILL.md"))) || null;
}

function skillTargetDir(opts) {
  if (opts.skillDir) return path.resolve(opts.skillDir);
  const configDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
  return path.join(configDir, "skills");
}

function installSkill(opts) {
  step("Installing agent skill");

  const source = findBundledSkill();
  if (!source) {
    fail("Bundled skill not found in this package.");
    return false;
  }

  const targetRoot = skillTargetDir(opts);
  const target = path.join(targetRoot, SKILL_NAME);

  try {
    fs.mkdirSync(targetRoot, { recursive: true });
    fs.rmSync(target, { recursive: true, force: true });
    fs.cpSync(source, target, { recursive: true });
  } catch (err) {
    fail(`Could not write the skill: ${err.message}`);
    return false;
  }

  ok(`Skill installed to ${target}`);
  return true;
}

// --- step 3: register the MCP server with detected clients -----------------

function registerMcp() {
  step("Registering MCP server");

  if (exists("claude")) {
    // `claude mcp add` is idempotent enough: re-adding an existing name errors
    // harmlessly, so a quiet failure here just means "already registered".
    const added = run(
      "claude",
      ["mcp", "add", "--scope", "user", "bcrp", "--", "bcrp-mcp"],
      { quiet: true }
    );
    if (added) {
      ok("Registered with Claude Code (user scope)");
    } else {
      skip("Claude Code: already registered (or add skipped)");
    }
  } else {
    skip("Claude Code CLI not found");
  }

  console.log(
    dim(
      "\n  For other clients, add this to their MCP config:\n" +
        '    { "mcpServers": { "bcrp": { "command": "bcrp-mcp" } } }'
    )
  );
  return true;
}

// --- main ------------------------------------------------------------------

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    printHelp();
    return;
  }

  console.log(bold("\nBCRP — Peruvian central bank data for AI agents"));
  console.log(dim("MCP server · CLI · agent skill\n"));

  const results = [];

  if (opts.python) {
    results.push(["MCP server + CLI", installPython(opts)]);
  } else {
    skip("Skipping Python package (--skill-only)");
  }

  if (opts.skill) {
    results.push(["Agent skill", installSkill(opts)]);
  } else {
    skip("Skipping agent skill (--no-skill)");
  }

  if (opts.python && opts.register && results.every(([, good]) => good)) {
    registerMcp();
  }

  step("Summary");
  for (const [label, good] of results) {
    good ? ok(label) : fail(label);
  }

  const allGood = results.every(([, good]) => good);
  if (allGood && opts.python) {
    console.log(
      `\n${bold("Try it:")}\n` +
        `  ${dim("$")} bcrp macro snapshot\n` +
        `  ${dim("$")} bcrp catalog search "tipo de cambio"\n` +
        `  ${dim("$")} bcrp --help\n`
    );
  } else if (allGood) {
    console.log(`\n${dim("Restart your AI client to pick up the new skill.")}\n`);
  }

  process.exit(allGood ? 0 : 1);
}

main();
