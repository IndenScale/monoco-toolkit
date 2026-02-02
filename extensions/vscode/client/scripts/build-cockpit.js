/**
 * Build script for Cockpit Settings React app
 * Uses esbuild for fast bundling
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

console.log('[Build Cockpit] Starting React build...')

const CLIENT_ROOT = path.resolve(__dirname, '..')
const COCKPIT_SRC = path.join(CLIENT_ROOT, 'src/cockpit')
const OUT_DIR = path.join(CLIENT_ROOT, 'out/cockpit')

// 1. Clean previous build
console.log('1. Cleaning output...')
if (fs.existsSync(OUT_DIR)) {
  fs.rmSync(OUT_DIR, { recursive: true, force: true })
}
fs.mkdirSync(OUT_DIR, { recursive: true })

// 2. Build with esbuild
console.log('2. Building with esbuild...')
try {
  const esbuildPath = path.resolve(CLIENT_ROOT, '../node_modules/.bin/esbuild')

  // Build the React app
  execSync(
    `${esbuildPath} ` +
    `${path.join(COCKPIT_SRC, 'index.tsx')} ` +
    `--bundle ` +
    `--outfile=${path.join(OUT_DIR, 'index.js')} ` +
    `--format=esm ` +
    `--target=es2020 ` +
    `--platform=browser ` +
    `--external:vscode ` +
    `--loader:.tsx=tsx ` +
    `--loader:.ts=ts ` +
    `--jsx=automatic ` +
    `--minify`,
    {
      cwd: CLIENT_ROOT,
      stdio: 'inherit',
    }
  )
} catch (e) {
  console.error('esbuild failed:', e)
  process.exit(1)
}

// 3. Copy CSS
console.log('3. Copying styles...')
const cssSrc = path.join(COCKPIT_SRC, 'styles', 'cockpit.css')
const cssDest = path.join(OUT_DIR, 'cockpit.css')
if (fs.existsSync(cssSrc)) {
  fs.copyFileSync(cssSrc, cssDest)
}

// 4. Copy index.html and update paths
console.log('4. Processing HTML...')
const htmlSrc = path.join(COCKPIT_SRC, 'index.html')
let htmlContent = fs.readFileSync(htmlSrc, 'utf-8')

// Replace paths for VS Code webview
htmlContent = htmlContent.replace(
  '<!-- CONFIG_INJECTION -->',
  '<link rel="stylesheet" href="cockpit.css">'
)
htmlContent = htmlContent.replace(
  'src="./index.js"',
  'src="index.js"'
)

fs.writeFileSync(path.join(OUT_DIR, 'index.html'), htmlContent)

console.log('[Build Cockpit] Success!')
console.log(`Output: ${OUT_DIR}`)
