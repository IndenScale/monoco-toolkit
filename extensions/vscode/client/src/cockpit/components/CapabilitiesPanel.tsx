/**
 * Capabilities Configuration Panel
 * Configure Skills and System Access (Bash-as-Tool)
 */

import React from 'react'
import {
  VSCodeCheckbox,
  VSCodeTextField,
  VSCodeDivider,
  VSCodeButton,
  VSCodeTag,
  VSCodePanels,
  VSCodePanelTab,
  VSCodePanelView,
} from '@vscode/webview-ui-toolkit/react'
import { SkillSet, SystemAccess } from '../types/config'

interface CapabilitiesPanelProps {
  skills: {
    directory: string
    sets: SkillSet[]
  }
  systemAccess: SystemAccess
  availableSkills: Array<{ id: string; name: string; description: string }>
  onSkillsDirectoryChange: (directory: string) => void
  onToggleSkill: (skillId: string) => void
  onSystemAccessChange: (updates: Partial<SystemAccess>) => void
  onScanSkills: () => void
}

export const CapabilitiesPanel: React.FC<CapabilitiesPanelProps> = ({
  skills,
  systemAccess,
  availableSkills,
  onSkillsDirectoryChange,
  onToggleSkill,
  onSystemAccessChange,
  onScanSkills,
}) => {
  const enabledCount = skills.sets.filter((s) => s.enabled).length

  return (
    <div className="capabilities-panel">
      <VSCodePanels>
        <VSCodePanelTab id="tab-skills">
          <span className="tab-icon">🧩</span> Skills
          {enabledCount > 0 && (
            <VSCodeTag className="tab-badge">{enabledCount}</VSCodeTag>
          )}
        </VSCodePanelTab>
        <VSCodePanelTab id="tab-system">
          <span className="tab-icon">🔧</span> System Access
        </VSCodePanelTab>

        <VSCodePanelView id="view-skills">
          <section className="config-section">
            <h3 className="section-title">
              <span className="icon">🧩</span>
              Skill Sets
            </h3>
            <p className="section-description">
              Manage agent capabilities through skill packages. Enable or disable specific skills to customize agent behavior.
            </p>

            <div className="form-group">
              <label htmlFor="skills-directory">Skills Directory</label>
              <div className="input-with-button">
                <VSCodeTextField
                  id="skills-directory"
                  value={skills.directory}
                  onChange={(e: any) => onSkillsDirectoryChange(e.target.value)}
                  placeholder="~/.monoco/skills"
                />
                <VSCodeButton appearance="secondary" onClick={onScanSkills}>
                  <span className="icon">🔍</span> Scan
                </VSCodeButton>
              </div>
            </div>

            <div className="skills-list">
              {skills.sets.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-icon">📦</span>
                  <p>No skills configured</p>
                  <p className="empty-hint">
                    Set the skills directory and click Scan to discover available skills.
                  </p>
                </div>
              ) : (
                skills.sets.map((skill) => (
                  <div key={skill.id} className={`skill-card ${skill.enabled ? 'enabled' : ''}`}>
                    <div className="skill-header">
                      <VSCodeCheckbox
                        checked={skill.enabled}
                        onChange={() => onToggleSkill(skill.id)}
                      />
                      <div className="skill-info">
                        <span className="skill-name">{skill.name}</span>
                        {skill.version && (
                          <VSCodeTag className="version-tag">v{skill.version}</VSCodeTag>
                        )}
                      </div>
                    </div>
                    <p className="skill-description">{skill.description}</p>
                    {skill.path && (
                      <code className="skill-path">{skill.path}</code>
                    )}
                  </div>
                ))
              )}

              {availableSkills.length > 0 && skills.sets.length === 0 && (
                <>
                  <p className="subsection-title">Available Skills</p>
                  {availableSkills.map((skill) => (
                    <div key={skill.id} className="skill-card available">
                      <div className="skill-header">
                        <VSCodeCheckbox
                          checked={false}
                          onChange={() => onToggleSkill(skill.id)}
                        />
                        <span className="skill-name">{skill.name}</span>
                      </div>
                      <p className="skill-description">{skill.description}</p>
                    </div>
                  ))}
                </>
              )}
            </div>
          </section>
        </VSCodePanelView>

        <VSCodePanelView id="view-system">
          <section className="config-section">
            <h3 className="section-title">
              <span className="icon">🔧</span>
              Bash-as-Tool
            </h3>
            <p className="section-description">
              Configure system access capabilities. Agent uses native shell commands instead of MCP for maximum flexibility.
            </p>

            <div className="info-banner">
              <span className="info-icon">ℹ️</span>
              <span>
                <strong>Bash-as-Tool Philosophy:</strong> Agent directly executes shell commands,
                file operations, and network requests through the universal shell interface.
                No MCP (Model Context Protocol) abstraction layer.
              </span>
            </div>

            <div className="form-group">
              <VSCodeCheckbox
                checked={systemAccess.enabled}
                onChange={(e: any) => onSystemAccessChange({ enabled: e.target.checked })}
              >
                <span className="checkbox-label">Enable System Access</span>
              </VSCodeCheckbox>
            </div>

            {systemAccess.enabled && (
              <>
                <VSCodeDivider />

                <div className="access-options">
                  <div className="form-group">
                    <VSCodeCheckbox
                      checked={systemAccess.allowFileSystem}
                      onChange={(e: any) => onSystemAccessChange({ allowFileSystem: e.target.checked })}
                    >
                      <div className="checkbox-content">
                        <span className="checkbox-label">File System Access</span>
                        <span className="checkbox-description">
                          Read, write, and manipulate files in the workspace
                        </span>
                      </div>
                    </VSCodeCheckbox>
                  </div>

                  <div className="form-group">
                    <VSCodeCheckbox
                      checked={systemAccess.allowNetwork}
                      onChange={(e: any) => onSystemAccessChange({ allowNetwork: e.target.checked })}
                    >
                      <div className="checkbox-content">
                        <span className="checkbox-label">Network Access</span>
                        <span className="checkbox-description">
                          Make HTTP requests, download resources, API calls
                        </span>
                      </div>
                    </VSCodeCheckbox>
                  </div>

                  <div className="form-group">
                    <VSCodeCheckbox
                      checked={systemAccess.allowSystemCommands}
                      onChange={(e: any) => onSystemAccessChange({ allowSystemCommands: e.target.checked })}
                    >
                      <div className="checkbox-content">
                        <span className="checkbox-label">System Commands</span>
                        <span className="checkbox-description">
                          Execute system-level commands (git, npm, docker, etc.)
                        </span>
                      </div>
                    </VSCodeCheckbox>
                  </div>
                </div>

                <VSCodeDivider />

                <div className="form-group">
                  <label>Restricted Commands</label>
                  <p className="field-hint">
                    Commands that require explicit confirmation before execution
                  </p>
                  <VSCodeTextField
                    value={systemAccess.restrictedCommands.join(', ')}
                    onChange={(e: any) =>
                      onSystemAccessChange({
                        restrictedCommands: e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean),
                      })
                    }
                    placeholder="rm -rf /, dd, mkfs"
                  />
                </div>
              </>
            )}
          </section>
        </VSCodePanelView>
      </VSCodePanels>
    </div>
  )
}
