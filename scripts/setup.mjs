/** Instalacion de dependencias: venv con uv + node_modules con bun. */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

const root = import.meta.dir ? join(import.meta.dir, "..") : process.cwd();
const isWindows = process.platform === "win32";

function run(command, args, cwd) {
  console.log(`\n> ${command} ${args.join(" ")}`);
  const result = spawnSync(command, args, {
    cwd,
    stdio: "inherit",
    shell: isWindows,
  });
  if (result.status !== 0) {
    console.error(`Fallo: ${command} ${args.join(" ")}`);
    process.exit(result.status ?? 1);
  }
}

// 1) Herramientas via mise (si esta disponible).
const mise = isWindows ? "mise.exe" : "mise";
const hasMise = spawnSync(mise, ["--version"], { stdio: "ignore", shell: isWindows }).status === 0;
if (hasMise) {
  run(mise, ["install"], root);
} else {
  console.warn("mise no encontrado: se usara el node/python/uv del PATH.");
}

// 2) Backend: uv crea backend/.venv y resuelve uv.lock.
const uv = hasMise ? [mise, ["exec", "--", "uv"]] : ["uv", []];
const uvCommand = uv[0];
const uvPrefix = uv[1];
run(uvCommand, [...uvPrefix, "sync", "--project", "backend"], root);

// 3) Frontend.
if (!existsSync(join(root, "frontend", "node_modules"))) {
  run("bun", ["install"], join(root, "frontend"));
} else {
  run("bun", ["install"], join(root, "frontend"));
}

console.log("\n  Listo. Arranca con:  bun run dev\n");
