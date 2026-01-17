const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

console.log("[Build Webview] Starting deterministic build...");

const CLIENT_ROOT = path.resolve(__dirname, "..");
const WEBVIEW_SRC = path.join(CLIENT_ROOT, "src/webview");
const SHARED_SRC = path.resolve(CLIENT_ROOT, "../shared");
const WEBVIEW_SHARED_DEST = path.join(WEBVIEW_SRC, "shared");
const OUT_DIR = path.join(CLIENT_ROOT, "out/webview");

// 1. Clean previous build
console.log("1. Cleaning output...");
if (fs.existsSync(OUT_DIR))
  fs.rmSync(OUT_DIR, { recursive: true, force: true });
if (fs.existsSync(WEBVIEW_SHARED_DEST))
  fs.rmSync(WEBVIEW_SHARED_DEST, { recursive: true, force: true });

// 2. Copy Shared Source to Webview Src (Explicit Dependency)
console.log("2. Copying shared source to local context...");
fs.cpSync(SHARED_SRC, WEBVIEW_SHARED_DEST, { recursive: true });

// 3. Update Imports (Runtime Rewrite)
// We will let TSC compile first.
// TSC compilation configuration.
// We need a temporary tsconfig that includes the local shared folder.
const TSCONFIG_PATH = path.join(WEBVIEW_SRC, "tsconfig.build.json");
const tsConfig = {
  compilerOptions: {
    module: "es2020",
    target: "es2020",
    moduleResolution: "node",
    outDir: OUT_DIR, // Use absolute path
    rootDir: ".",
    skipLibCheck: true,
    resolveJsonModule: true,
    baseUrl: ".",
    paths: {
      "@shared/*": ["shared/*"],
    },
  },
  include: ["**/*"],
  exclude: ["KanbanProvider.ts", "**/*.test.ts"],
};
fs.writeFileSync(TSCONFIG_PATH, JSON.stringify(tsConfig, null, 2));

// 4. Compile
console.log("3. Compiling...");
try {
  // Run tsc from client/src/webview directory so paths are relative to it
  const tscPath = path.resolve(CLIENT_ROOT, "../node_modules/.bin/tsc");
  execSync(`${tscPath} -p tsconfig.build.json`, {
    cwd: WEBVIEW_SRC,
    stdio: "inherit",
  });
} catch (e) {
  console.error("TSC Failed.");
  // Cleanup even on failure
  cleanup();
  process.exit(1);
}

// 5. Post-Process: Add .js extensions for Browser
console.log("4. Post-processing imports (adding .js)...");
function addJsExtensions(dir) {
  const files = fs.readdirSync(dir);
  files.forEach((file) => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory()) {
      addJsExtensions(filePath);
    } else if (file.endsWith(".js")) {
      let content = fs.readFileSync(filePath, "utf-8");

      // 1. Resolve @shared alias
      content = content.replace(
        /from\s+["']@shared\/([^"']+)["']/g,
        (match, p1) => {
          // Target is OUT_DIR/shared/p1
          const targetPath = path.join(OUT_DIR, "shared", p1);
          let relativePath = path.relative(path.dirname(filePath), targetPath);
          if (!relativePath.startsWith(".")) {
            relativePath = "./" + relativePath;
          }
          return `from "${relativePath}"`; // Will be processed by step 2 for .js
        },
      );

      // 2. Add .js extensions
      // Regex to match relative imports: from "./..." or "../..."
      // Exclude already having .js
      content = content.replace(/from\s+["'](\.[^"']+)["']/g, (match, p1) => {
        if (p1.endsWith(".js")) return match;
        // Check if directory (index.js implied)
        try {
          // This check is tricky on compiled output because source structure mirrors it.
          // Simple heuristic: just add .js. If it was a directory import, browser needs /index.js.
          // For now, assume file imports.

          // Exception: imports ending in /index should ideally not have /index.js appended if p1 is a folder?
          // But tsc output usually points to file.
          return `from "${p1}.js"`;
        } catch (e) {
          return match;
        }
      });
      fs.writeFileSync(filePath, content);
    }
  });
}
addJsExtensions(OUT_DIR);

// 6. Cleanup
function cleanup() {
  console.log("5. Cleanup...");
  if (fs.existsSync(WEBVIEW_SHARED_DEST))
    fs.rmSync(WEBVIEW_SHARED_DEST, { recursive: true, force: true });
  if (fs.existsSync(TSCONFIG_PATH)) fs.rmSync(TSCONFIG_PATH);
}
// cleanup();

console.log("[Build Webview] Success.");
