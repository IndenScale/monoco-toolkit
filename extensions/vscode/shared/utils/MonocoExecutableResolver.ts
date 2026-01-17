/**
 * Unified Monoco executable resolver
 * Eliminates code duplication between bootstrap.ts and server.ts
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";

export interface ResolverOptions {
  workspaceRoot?: string;
  configuredPath?: string;
  bundledPath?: string;
}

/**
 * Resolve the Monoco executable path with the following priority:
 * 1. Configured path (from settings)
 * 2. Local development version (.venv/bin/monoco)
 * 3. Bundled binary
 * 4. UV tool installation (~/.local/bin/monoco)
 * 5. System PATH
 */
export async function resolveMonocoExecutable(
  options: ResolverOptions = {}
): Promise<string> {
  const { workspaceRoot, configuredPath, bundledPath } = options;

  // 1. Check configured path
  if (configuredPath && configuredPath !== "monoco") {
    return configuredPath;
  }

  // 2. Check local workspace paths (Engineering Dev Version) - HIGHEST PRIORITY
  if (workspaceRoot) {
    const devPaths = [
      path.join(workspaceRoot, ".venv", "bin", "monoco"),
      path.join(workspaceRoot, "Toolkit", ".venv", "bin", "monoco"),
      path.join(workspaceRoot, "dist", "monoco"),
      path.join(workspaceRoot, "Toolkit", "dist", "monoco"),
    ];

    for (const devPath of devPaths) {
      if (fs.existsSync(devPath)) {
        return devPath;
      }
    }
  }

  // 3. Check bundled binary
  if (bundledPath && fs.existsSync(bundledPath)) {
    return bundledPath;
  }

  // 4. Check common uv tool location
  const home = os.homedir();
  const uvPath = path.join(home, ".local", "bin", "monoco");
  if (fs.existsSync(uvPath)) {
    return uvPath;
  }

  // 5. Fallback to system PATH
  return "monoco";
}

/**
 * Check if a command is available by trying to execute it
 */
export async function isCommandAvailable(
  cmd: string,
  flag: string = "--version",
  execFn: (cmd: string, callback: (error: Error | null) => void) => void
): Promise<boolean> {
  return new Promise((resolve) => {
    execFn(`${cmd} ${flag}`, (err) => {
      resolve(!err);
    });
  });
}
