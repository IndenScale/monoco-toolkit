/**
 * CLI Arguments Preview Panel
 * Shows how settings translate to CLI arguments
 */

import React, { useState, useEffect } from 'react'
import { VSCodeButton, VSCodeTag } from '@vscode/webview-ui-toolkit/react'
import { CockpitSettings } from '../types/config'

interface CliPreviewProps {
  settings: CockpitSettings
  onRefresh: () => void
}

export const CliPreview: React.FC<CliPreviewProps> = ({ settings, onRefresh }) => {
  const [args, setArgs] = useState<string[]>([])
  const [isExpanded, setIsExpanded] = useState(false)

  useEffect(() => {
    // Generate CLI args from settings
    const generatedArgs: string[] = []

    // Provider
    generatedArgs.push('--provider', settings.runtime.provider)

    // Role
    if (settings.runtime.role !== 'default') {
      generatedArgs.push('--role', settings.runtime.role)
    }

    // Autonomy
    if (settings.runtime.autonomy.level === 'yolo') {
      generatedArgs.push('--yolo')
    } else if (settings.runtime.autonomy.level === 'full-manual') {
      generatedArgs.push('--manual-approval')
    }

    // Persistence
    if (settings.runtime.autonomy.persistence !== 'unlimited') {
      generatedArgs.push('--persistence', settings.runtime.autonomy.persistence)
    }

    // Skills
    if (settings.capabilities.skills.directory) {
      generatedArgs.push('--skills-dir', settings.capabilities.skills.directory)
    }
    const enabledSkills = settings.capabilities.skills.sets
      .filter((s) => s.enabled)
      .map((s) => s.id)
    if (enabledSkills.length > 0) {
      generatedArgs.push('--skills', enabledSkills.join(','))
    }

    // System Access
    if (!settings.capabilities.systemAccess.enabled) {
      generatedArgs.push('--no-system-access')
    } else {
      if (!settings.capabilities.systemAccess.allowNetwork) {
        generatedArgs.push('--no-network')
      }
      if (!settings.capabilities.systemAccess.allowFileSystem) {
        generatedArgs.push('--no-fs')
      }
      if (!settings.capabilities.systemAccess.allowSystemCommands) {
        generatedArgs.push('--no-commands')
      }
      if (settings.capabilities.systemAccess.restrictedCommands.length > 0) {
        generatedArgs.push(
          '--restricted-commands',
          settings.capabilities.systemAccess.restrictedCommands.join(',')
        )
      }
    }

    // Culture
    if (settings.culture.language !== 'auto') {
      generatedArgs.push('--lang', settings.culture.language)
    }
    if (settings.culture.tone !== 'professional') {
      generatedArgs.push('--tone', settings.culture.tone)
    }
    if (settings.culture.responseStyle !== 'balanced') {
      generatedArgs.push('--style', settings.culture.responseStyle)
    }

    setArgs(generatedArgs)
  }, [settings])

  const copyToClipboard = () => {
    const command = `monoco agent run ${args.join(' ')}`
    navigator.clipboard.writeText(command)
  }

  return (
    <div className="cli-preview">
      <div className="cli-preview-header" onClick={() => setIsExpanded(!isExpanded)}>
        <span className="cli-icon">⚡</span>
        <span className="cli-title">CLI Preview</span>
        <VSCodeTag className="cli-count">{args.length} args</VSCodeTag>
        <span className={`cli-chevron ${isExpanded ? 'expanded' : ''}`}>▶</span>
      </div>

      {isExpanded && (
        <div className="cli-preview-content">
          <p className="cli-description">
            These CLI arguments are generated from your current settings.
            They will be used when launching the agent from command line.
          </p>

          <div className="cli-command-box">
            <code className="cli-command">
              <span className="cli-prompt">$</span>
              <span className="cli-binary">monoco</span>
              <span className="cli-subcommand">agent run</span>
              {args.map((arg, i) => (
                <span key={i} className={arg.startsWith('--') ? 'cli-flag' : 'cli-arg'}>
                  {arg}
                </span>
              ))}
            </code>
          </div>

          <div className="cli-actions">
            <VSCodeButton appearance="secondary" onClick={copyToClipboard}>
              <span className="icon">📋</span> Copy Command
            </VSCodeButton>
            <VSCodeButton appearance="secondary" onClick={onRefresh}>
              <span className="icon">🔄</span> Refresh
            </VSCodeButton>
          </div>

          <div className="cli-args-list">
            <h4>Argument Breakdown</h4>
            {args.length === 0 ? (
              <p className="cli-empty">Using all defaults - no custom arguments needed.</p>
            ) : (
              <ul>
                {args.map((arg, i) => (
                  <li key={i} className={arg.startsWith('--') ? 'arg-flag' : 'arg-value'}>
                    {arg.startsWith('--') ? (
                      <>
                        <code className="flag-name">{arg}</code>
                        {args[i + 1] && !args[i + 1].startsWith('--') && (
                          <code className="flag-value">{args[i + 1]}</code>
                        )}
                      </>
                    ) : (
                      !args[i - 1]?.startsWith('--') && <code>{arg}</code>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
