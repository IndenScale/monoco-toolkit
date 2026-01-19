const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const DOCS_EN = path.join(ROOT, "docs", "en");
const DOCS_ZH = path.join(ROOT, "docs", "zh");
const SITE_SRC = path.join(ROOT, "site", "src");

function copyRecursiveSync(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();
  if (isDirectory) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.readdirSync(src).forEach((childItemName) => {
      copyRecursiveSync(
        path.join(src, childItemName),
        path.join(dest, childItemName),
      );
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}

console.log("🚀 Syncing documentation content...");

// Clean and recreate site/src
if (fs.existsSync(SITE_SRC)) {
  fs.rmSync(SITE_SRC, { recursive: true, force: true });
}
fs.mkdirSync(SITE_SRC, { recursive: true });

// Copy English to root of src
if (fs.existsSync(DOCS_EN)) {
  console.log("  - Copying English docs to root...");
  copyRecursiveSync(DOCS_EN, SITE_SRC);
}

// Copy Chinese to /zh/
if (fs.existsSync(DOCS_ZH)) {
  console.log("  - Copying Chinese docs to /zh...");
  copyRecursiveSync(DOCS_ZH, path.join(SITE_SRC, "zh"));
}

console.log("✨ Documentation sync complete!");
