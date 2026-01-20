console.log('[Copy Server Assets] Starting...')
const fs = require('fs')
const path = require('path')

const srcDir = path.join(__dirname, '../server/src/schema')
const destDir = path.join(__dirname, '../server/out/schema')

if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true })
}

if (fs.existsSync(srcDir)) {
  fs.readdirSync(srcDir).forEach((file) => {
    const srcFile = path.join(srcDir, file)
    const destFile = path.join(destDir, file)
    if (fs.lstatSync(srcFile).isFile()) {
      fs.copyFileSync(srcFile, destFile)
    }
  })
} else {
  console.warn(`Source directory not found: ${srcDir}`)
}
console.log('[Copy Server Assets] Finished.')
