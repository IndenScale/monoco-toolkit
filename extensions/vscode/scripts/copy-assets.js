const fs = require('fs')
const path = require('path')

const filesToCopy = [
  { src: '../client/src/webview/index.html', dest: '../client/out/webview/index.html' },
  { src: '../client/src/webview/style.css', dest: '../client/out/webview/style.css' },
]

filesToCopy.forEach((file) => {
  const srcPath = path.join(__dirname, file.src)
  const destPath = path.join(__dirname, file.dest)
  const destDir = path.dirname(destPath)

  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true })
  }

  if (fs.existsSync(srcPath)) {
    fs.copyFileSync(srcPath, destPath)
  } else {
    console.warn(`Source file not found: ${srcPath}`)
  }
})
