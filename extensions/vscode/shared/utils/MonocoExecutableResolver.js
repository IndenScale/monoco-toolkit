'use strict'
/**
 * Unified Monoco executable resolver
 * Eliminates code duplication between bootstrap.ts and server.ts
 */
var __createBinding =
  (this && this.__createBinding) ||
  (Object.create
    ? function (o, m, k, k2) {
        if (k2 === undefined) k2 = k
        var desc = Object.getOwnPropertyDescriptor(m, k)
        if (!desc || ('get' in desc ? !m.__esModule : desc.writable || desc.configurable)) {
          desc = {
            enumerable: true,
            get: function () {
              return m[k]
            },
          }
        }
        Object.defineProperty(o, k2, desc)
      }
    : function (o, m, k, k2) {
        if (k2 === undefined) k2 = k
        o[k2] = m[k]
      })
var __setModuleDefault =
  (this && this.__setModuleDefault) ||
  (Object.create
    ? function (o, v) {
        Object.defineProperty(o, 'default', { enumerable: true, value: v })
      }
    : function (o, v) {
        o['default'] = v
      })
var __importStar =
  (this && this.__importStar) ||
  (function () {
    var ownKeys = function (o) {
      ownKeys =
        Object.getOwnPropertyNames ||
        function (o) {
          var ar = []
          for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k
          return ar
        }
      return ownKeys(o)
    }
    return function (mod) {
      if (mod && mod.__esModule) return mod
      var result = {}
      if (mod != null)
        for (var k = ownKeys(mod), i = 0; i < k.length; i++)
          if (k[i] !== 'default') __createBinding(result, mod, k[i])
      __setModuleDefault(result, mod)
      return result
    }
  })()
Object.defineProperty(exports, '__esModule', { value: true })
exports.resolveMonocoExecutable = resolveMonocoExecutable
exports.isCommandAvailable = isCommandAvailable
const fs = __importStar(require('fs'))
const path = __importStar(require('path'))
const os = __importStar(require('os'))
/**
 * Resolve the Monoco executable path with the following priority:
 * 1. Configured path (from settings)
 * 2. Local development version (.venv/bin/monoco)
 * 3. Bundled binary
 * 4. UV tool installation (~/.local/bin/monoco)
 * 5. System PATH
 */
async function resolveMonocoExecutable(options = {}) {
  const { workspaceRoot, configuredPath, bundledPath } = options
  // 1. Check configured path
  if (configuredPath && configuredPath !== 'monoco') {
    return configuredPath
  }
  // 2. Check local workspace paths (Engineering Dev Version) - HIGHEST PRIORITY
  if (workspaceRoot) {
    const devPaths = [
      path.join(workspaceRoot, '.venv', 'bin', 'monoco'),
      path.join(workspaceRoot, 'Toolkit', '.venv', 'bin', 'monoco'),
      path.join(workspaceRoot, 'dist', 'monoco'),
      path.join(workspaceRoot, 'Toolkit', 'dist', 'monoco'),
    ]
    for (const devPath of devPaths) {
      if (fs.existsSync(devPath)) {
        return devPath
      }
    }
  }
  // 3. Check bundled binary
  if (bundledPath && fs.existsSync(bundledPath)) {
    return bundledPath
  }
  // 4. Check common uv tool location
  const home = os.homedir()
  const uvPath = path.join(home, '.local', 'bin', 'monoco')
  if (fs.existsSync(uvPath)) {
    return uvPath
  }
  // 5. Fallback to system PATH
  return 'monoco'
}
/**
 * Check if a command is available by trying to execute it
 */
async function isCommandAvailable(cmd, flag = '--version', execFn) {
  return new Promise((resolve) => {
    execFn(`${cmd} ${flag}`, (err) => {
      resolve(!err)
    })
  })
}
//# sourceMappingURL=MonocoExecutableResolver.js.map
