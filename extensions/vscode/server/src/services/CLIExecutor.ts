/**
 * CLI Executor Service
 * Handles all communication with the Monoco CLI
 */

import { spawn } from 'child_process'
import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'

export interface CLIExecutionResult {
  stdout: string
  stderr: string
  code: number
}

export interface MonocoSettings {
  executablePath: string
  webUrl: string
}

export class CLIExecutor {
  private settings: MonocoSettings
  private logger?: (message: string) => void

  constructor(settings: MonocoSettings, logger?: (message: string) => void) {
    this.settings = settings
    this.logger = logger
  }

  /**
   * Update settings
   */
  updateSettings(settings: MonocoSettings) {
    this.settings = settings
  }

  /**
   * Execute a Monoco CLI command (raw)
   */
  async executeRaw(args: string[], root: string): Promise<CLIExecutionResult> {
    const executable = await this.resolveExecutable(root)

    return new Promise((resolve, reject) => {
      const finalArgs = ['--root', root, ...args]
      this.log(`Executing: ${executable} ${finalArgs.join(' ')}`)

      const proc = spawn(executable, finalArgs, {
        cwd: root,
        env: process.env,
      })

      let stdout = ''
      let stderr = ''

      proc.stdout.on('data', (data) => {
        stdout += data.toString()
      })

      proc.stderr.on('data', (data) => {
        stderr += data.toString()
      })

      proc.on('close', (code) => {
        resolve({ stdout, stderr, code: code ?? -1 })
      })

      proc.on('error', (err) => {
        reject(new Error(`Failed to spawn command: ${err.message}`))
      })
    })
  }

  /**
   * Execute a Monoco CLI command (throws on error)
   */
  async execute(args: string[], root: string): Promise<string> {
    const { stdout, stderr, code } = await this.executeRaw(args, root)
    if (code !== 0) {
      throw new Error(`Command failed with code ${code}: ${stderr}`)
    }
    return stdout
  }

  /**
   * Resolve the Monoco executable path
   */
  private async resolveExecutable(root: string): Promise<string> {
    let executable = this.settings.executablePath

    // If executable is default "monoco", we start resolution
    if (executable === 'monoco') {
      // 1. Check local workspace paths (Engineering Dev Version)
      const venvPath = path.join(root, '.venv', 'bin', 'monoco')
      const toolkitVenvPath = path.join(root, 'Toolkit', '.venv', 'bin', 'monoco')
      const devBuildPath = path.join(root, 'dist', 'monoco')
      const subProjectPath = path.join(root, 'Toolkit', 'dist', 'monoco')

      if (fs.existsSync(venvPath)) {
        return venvPath
      }
      if (fs.existsSync(toolkitVenvPath)) {
        return toolkitVenvPath
      }
      if (fs.existsSync(devBuildPath)) {
        return devBuildPath
      }
      if (fs.existsSync(subProjectPath)) {
        return subProjectPath
      }

      // 2. Check bundled path from environment
      const bundledPath = process.env['MONOCO_BUNDLED_PATH']
      if (bundledPath && fs.existsSync(bundledPath)) {
        return bundledPath
      }

      // 3. Check common uv tool location
      const home = os.homedir()
      const uvPath = path.join(home, '.local', 'bin', 'monoco')
      if (fs.existsSync(uvPath)) {
        return uvPath
      }
    }

    return executable
  }

  /**
   * Log a message
   */
  private log(message: string) {
    if (this.logger) {
      this.logger(`[Monoco LSP] ${message}`)
    }
  }
}
