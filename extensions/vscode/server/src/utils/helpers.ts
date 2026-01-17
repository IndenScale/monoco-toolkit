/**
 * Utility functions for the LSP server
 */

import * as fs from "fs";
import * as path from "path";

/**
 * Find the project root directory (containing .monoco folder)
 */
export function findProjectRoot(startPath: string): string | null {
  let current = startPath;
  if (fs.existsSync(startPath) && fs.statSync(startPath).isFile()) {
    current = path.dirname(startPath);
  }

  while (true) {
    if (fs.existsSync(path.join(current, ".monoco"))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return null;
    }
    current = parent;
  }
}
