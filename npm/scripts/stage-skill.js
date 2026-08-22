#!/usr/bin/env node
/**
 * Copy the canonical skill (repo root `skills/`) into the npm package before
 * packing. npm can only ship files inside the package directory, and we don't
 * want a second hand-maintained copy of the skill drifting out of sync, so the
 * repo keeps one source of truth and this stages it at pack time.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const pkgDir = path.resolve(__dirname, "..");
const source = path.resolve(pkgDir, "..", "skills");
const target = path.join(pkgDir, "skills");

if (!fs.existsSync(source)) {
  console.error(`stage-skill: no skills/ directory at ${source}`);
  process.exit(1);
}

fs.rmSync(target, { recursive: true, force: true });
fs.cpSync(source, target, { recursive: true });

const count = fs.readdirSync(target).length;
console.log(`stage-skill: staged ${count} skill(s) into ${path.relative(pkgDir, target)}`);
