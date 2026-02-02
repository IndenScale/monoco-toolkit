/**
 * Agent Runtime Configuration Panel
 * Configure Provider, Role, and Autonomy settings
 */

import React from 'react'
import {
  VSCodeDropdown,
  VSCodeOption,
  VSCodeRadioGroup,
  VSCodeRadio,
  VSCodeDivider,
} from '@vscode/webview-ui-toolkit/react'
import {
  AgentProvider,
  AgentRole,
  AutonomyLevel,
  PersistenceLevel,
  PROVIDER_METADATA,
  ROLE_METADATA,
  AUTONOMY_METADATA,
  PERSISTENCE_METADATA,
} from '../types/config'

interface RuntimePanelProps {
  provider: AgentProvider
  role: AgentRole
  autonomy: {
    level: AutonomyLevel
    persistence: PersistenceLevel
  }
  availableProviders: string[]
  onProviderChange: (provider: AgentProvider) => void
  onRoleChange: (role: AgentRole) => void
  onAutonomyLevelChange: (level: AutonomyLevel) => void
  onPersistenceChange: (persistence: PersistenceLevel) => void
}

export const RuntimePanel: React.FC<RuntimePanelProps> = ({
  provider,
  role,
  autonomy,
  availableProviders,
  onProviderChange,
  onRoleChange,
  onAutonomyLevelChange,
  onPersistenceChange,
}) => {
  const providers = (availableProviders.length > 0 ? availableProviders : Object.keys(PROVIDER_METADATA)) as AgentProvider[]
  const roles = Object.keys(ROLE_METADATA) as AgentRole[]
  const autonomyLevels = Object.keys(AUTONOMY_METADATA) as AutonomyLevel[]
  const persistenceLevels = Object.keys(PERSISTENCE_METADATA) as PersistenceLevel[]

  return (
    <div className="runtime-panel">
      <section className="config-section">
        <h3 className="section-title">
          <span className="icon">🤖</span>
          Agent Provider (Kernel)
        </h3>
        <p className="section-description">
          Select the backend service that powers your agent.
        </p>

        <div className="form-group">
          <label htmlFor="provider-select">Provider</label>
          <VSCodeDropdown
            id="provider-select"
            value={provider}
            onChange={(e: any) => onProviderChange(e.target.value as AgentProvider)}
          >
            {providers.map((p) => (
              <VSCodeOption key={p} value={p}>
                {PROVIDER_METADATA[p]?.icon || '📡'} {PROVIDER_METADATA[p]?.name || p}
              </VSCodeOption>
            ))}
          </VSCodeDropdown>
        </div>

        {provider && PROVIDER_METADATA[provider] && (
          <div className="info-card">
            <span className="info-icon">{PROVIDER_METADATA[provider].icon}</span>
            <span className="info-text">{PROVIDER_METADATA[provider].description}</span>
          </div>
        )}
      </section>

      <VSCodeDivider />

      <section className="config-section">
        <h3 className="section-title">
          <span className="icon">👤</span>
          Agent Role (Persona)
        </h3>
        <p className="section-description">
          Define the agent's expertise and behavioral characteristics.
        </p>

        <div className="form-group">
          <label htmlFor="role-select">Role</label>
          <VSCodeDropdown
            id="role-select"
            value={role}
            onChange={(e: any) => onRoleChange(e.target.value as AgentRole)}
          >
            {roles.map((r) => (
              <VSCodeOption key={r} value={r}>
                {ROLE_METADATA[r]?.icon || '👤'} {ROLE_METADATA[r]?.name || r}
              </VSCodeOption>
            ))}
          </VSCodeDropdown>
        </div>

        {role && ROLE_METADATA[role] && (
          <div className="info-card">
            <span className="info-icon">{ROLE_METADATA[role].icon}</span>
            <span className="info-text">{ROLE_METADATA[role].description}</span>
          </div>
        )}
      </section>

      <VSCodeDivider />

      <section className="config-section">
        <h3 className="section-title">
          <span className="icon">🎮</span>
          Autonomy & Control
        </h3>
        <p className="section-description">
          Configure human-in-the-loop behavior and execution limits.
        </p>

        <div className="form-group">
          <label>Human-in-the-Loop Mode</label>
          <VSCodeRadioGroup
            value={autonomy.level}
            onChange={(e: any) => onAutonomyLevelChange(e.target.value as AutonomyLevel)}
          >
            {autonomyLevels.map((level) => (
              <VSCodeRadio key={level} value={level}>
                <div className="radio-content">
                  <span className="radio-label">{AUTONOMY_METADATA[level].name}</span>
                  <span className="radio-description">{AUTONOMY_METADATA[level].description}</span>
                </div>
              </VSCodeRadio>
            ))}
          </VSCodeRadioGroup>
        </div>

        <div className="form-group">
          <label>Persistence Scope</label>
          <VSCodeRadioGroup
            value={autonomy.persistence}
            onChange={(e: any) => onPersistenceChange(e.target.value as PersistenceLevel)}
          >
            {persistenceLevels.map((level) => (
              <VSCodeRadio key={level} value={level}>
                <div className="radio-content">
                  <span className="radio-label">{PERSISTENCE_METADATA[level].name}</span>
                  <span className="radio-description">{PERSISTENCE_METADATA[level].description}</span>
                </div>
              </VSCodeRadio>
            ))}
          </VSCodeRadioGroup>
        </div>
      </section>
    </div>
  )
}
