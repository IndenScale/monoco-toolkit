const fs = require('fs')
const path = require('path')

const OUT_DIR = path.resolve(__dirname, '../out')
const SHARED_DIR = path.join(OUT_DIR, 'shared')

function walk(dir, callback) {
  const files = fs.readdirSync(dir)
  files.forEach((file) => {
    const filepath = path.join(dir, file)
    if (fs.statSync(filepath).isDirectory()) {
      walk(filepath, callback)
    } else {
      callback(filepath)
    }
  })
}

console.log('[Resolve Aliases] Starting...')

walk(OUT_DIR, (filepath) => {
  if (filepath.endsWith('.js') || filepath.endsWith('.d.ts')) {
    let content = fs.readFileSync(filepath, 'utf8')
    let changed = false

    // Replace @shared/*
    // Regex handles:
    // import ... from "@shared/..."
    // require("@shared/...")
    // import("@shared/...")

    const regex = /(?:from\s+["']|require\(["']|import\(["'])(@shared\/[^"']+)(?:["']\))/g

    let match
    // We need to loop or use replace with callback to handle calculation
    // Simpler to use replace directly

    const newContent = content.replace(
      /(from\s+["']|require\(["']|import\(["'])(@shared\/)([^"']+)(["']\))/g,
      (fullMatch, prefix, alias, rest, suffix) => {
        // Calculate relative path
        const fileDir = path.dirname(filepath)
        // Target is OUT_DIR/shared/rest
        // However, verify if 'rest' already contains extension or index logic?
        // Usually TS import is just path.

        const targetPath = path.join(SHARED_DIR, rest)
        let relativePath = path.relative(fileDir, targetPath)

        // Ensure logic starts with ./ or ../
        if (!relativePath.startsWith('.')) {
          relativePath = './' + relativePath
        }

        // Normalize path separators for Windows compatibility if needed (but we are on Mac)
        // relativePath = relativePath.split(path.sep).join('/');

        console.log(
          `Rewriting in ${path.relative(OUT_DIR, filepath)}: @shared/${rest} -> ${relativePath}`
        )
        changed = true
        return `${prefix}${relativePath}${suffix}`
      }
    )

    if (changed) {
      fs.writeFileSync(filepath, newContent)
    }
  }
})

console.log('[Resolve Aliases] Finished.')
