/**
 * Cockpit Settings Main Application
 * Entry point for the React-based settings webview
 */

import React from 'react'
import {
  VSCodePanels,
  VSCodePanelTab,
  VSCodePanelView,
  VSCodeButton,
  VSCodeProgressRing,
} from '@vscode/webview-ui-toolkit/react'
import { RuntimePanel, CapabilitiesPanel, CulturePanel, CliPreview } from '../components'
import { useCockpitSettings } from '../hooks'

export const CockpitApp: React.FC = () => {
  const {
    settings,
    isLoading,
    availableProviders,
    availableSkills,
    updateProvider,
    updateRole,
    updateAutonomyLevel,
    updatePersistence,
    updateSkills,
    toggleSkill,
    updateSystemAccess,
    updateCulture,
    saveSettings,
    previewCliArgs,
    hasChanges,
  } = useCockpitSettings()

  if (isLoading) {
    return (
      <div className="cockpit-loading">
        <VSCodeProgressRing />
        <p>Loading Cockpit Settings...</p>
      </div>
    )
  }

  return (
    <div className="cockpit-app">
      <header className="cockpit-header">
        <div className="header-content">
          <h1 className="header-title">
            <span className="header-icon">🎛️</span>
            Monoco Cockpit
          </h1>
          <p className="header-subtitle">
            Configure your Agent Runtime, Capabilities, and Preferences
          </p>
        </div>
        <div className="header-actions">
          {hasChanges && (
            <span className="unsaved-indicator">
              <span className="dot">●</span> Unsaved changes
            </span>
          )}
          <VSCodeButton appearance="primary" onClick={saveSettings} disabled={!hasChanges}>
            <span className="icon">💾</span> Save Settings
          </VSCodeButton>
        </div>
      </header>

      <main className="cockpit-main">
        <VSCodePanels className="cockpit-panels">
          <VSCodePanelTab id="tab-runtime">
            <span className="tab-icon">🤖</span> Agent Runtime
          </VSCodePanelTab>
          <VSCodePanelTab id="tab-capabilities">
            <span className="tab-icon">🧩</span> Capabilities
          </VSCodePanelTab>
          <VSCodePanelTab id="tab-culture">
            <span className="tab-icon">🌍</span> Culture
          </VSCodePanelTab>

          <VSCodePanelView id="view-runtime">
            <RuntimePanel
              provider={settings.runtime.provider}
              role={settings.runtime.role}
              autonomy={settings.runtime.autonomy}
              availableProviders={availableProviders}
              onProviderChange={updateProvider}
              onRoleChange={updateRole}
              onAutonomyLevelChange={updateAutonomyLevel}
              onPersistenceChange={updatePersistence}
            />
          </VSCodePanelView>

          <VSCodePanelView id="view-capabilities">
            <CapabilitiesPanel
              skills={settings.capabilities.skills}
              systemAccess={settings.capabilities.systemAccess}
              availableSkills={availableSkills}
              onSkillsDirectoryChange={(dir) => updateSkills({ directory: dir })}
              onToggleSkill={toggleSkill}
              onSystemAccessChange={updateSystemAccess}
              onScanSkills={() => {}}
            />
          </VSCodePanelView>

          <VSCodePanelView id="view-culture">
            <CulturePanel culture={settings.culture} onCultureChange={updateCulture} />
          </VSCodePanelView>
        </VSCodePanels>

        <CliPreview settings={settings} onRefresh={previewCliArgs} />
      </main>

      <footer className="cockpit-footer">
        <div className="footer-info">
          <span className="footer-item">
            <span className="icon">🤖</span> {settings.runtime.provider}
          </span>
          <span className="footer-separator">•</span>
          <span className="footer-item">
            <span className="icon">👤</span> {settings.runtime.role}
          </span>
          <span className="footer-separator">•</span>
          <span className="footer-item">
            <span className="icon">🎮</span> {settings.runtime.autonomy.level}
          </span>
        </div>
        <div className="footer-actions">
          <VSCodeButton appearance="secondary" onClick={previewCliArgs}>
            <span className="icon">⚡</span> Preview CLI
          </VSCodeButton>
        </div>
      </footer>
    </div>
  )
}
