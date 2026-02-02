/**
 * React hook for managing Cockpit Settings state
 */

import { useState, useCallback, useEffect } from 'react'
import {
  CockpitSettings,
  DEFAULT_COCKPIT_SETTINGS,
  AgentProvider,
  AgentRole,
  AutonomyLevel,
  PersistenceLevel,
  SkillSet,
  SystemAccess,
  CultureConfig,
} from '../types/config'
import { useVSCodeApi } from './useVSCodeApi'

export interface UseCockpitSettingsReturn {
  settings: CockpitSettings
  isLoading: boolean
  availableProviders: string[]
  availableSkills: Array<{ id: string; name: string; description: string }>
  updateRuntime: (updates: Partial<CockpitSettings['runtime']>) => void
  updateProvider: (provider: AgentProvider) => void
  updateRole: (role: AgentRole) => void
  updateAutonomy: (updates: Partial<CockpitSettings['runtime']['autonomy']>) => void
  updateAutonomyLevel: (level: AutonomyLevel) => void
  updatePersistence: (persistence: PersistenceLevel) => void
  updateSkills: (updates: Partial<CockpitSettings['capabilities']['skills']>) => void
  toggleSkill: (skillId: string) => void
  updateSystemAccess: (updates: Partial<SystemAccess>) => void
  updateCulture: (updates: Partial<CultureConfig>) => void
  saveSettings: () => void
  previewCliArgs: () => void
  hasChanges: boolean
}

export function useCockpitSettings(): UseCockpitSettingsReturn {
  const { postMessage, onMessage, isReady } = useVSCodeApi()
  const [settings, setSettings] = useState<CockpitSettings>(DEFAULT_COCKPIT_SETTINGS)
  const [originalSettings, setOriginalSettings] = useState<CockpitSettings>(DEFAULT_COCKPIT_SETTINGS)
  const [isLoading, setIsLoading] = useState(true)
  const [availableProviders, setAvailableProviders] = useState<string[]>([])
  const [availableSkills, setAvailableSkills] = useState<Array<{ id: string; name: string; description: string }>>([])

  // Load settings on mount
  useEffect(() => {
    if (!isReady) return

    // Request settings from extension
    postMessage({ type: 'cockpit:settings:load', payload: {} })
  }, [isReady, postMessage])

  // Listen for settings loaded
  useEffect(() => {
    return onMessage('cockpit:settings:loaded', (payload) => {
      setSettings(payload.settings)
      setOriginalSettings(payload.settings)
      setAvailableProviders(payload.availableProviders)
      setAvailableSkills(payload.availableSkills)
      setIsLoading(false)
    })
  }, [onMessage])

  // Check if there are changes
  const hasChanges = JSON.stringify(settings) !== JSON.stringify(originalSettings)

  // Runtime updates
  const updateRuntime = useCallback((updates: Partial<CockpitSettings['runtime']>) => {
    setSettings((prev) => ({
      ...prev,
      runtime: { ...prev.runtime, ...updates },
    }))
  }, [])

  const updateProvider = useCallback((provider: AgentProvider) => {
    setSettings((prev) => ({
      ...prev,
      runtime: { ...prev.runtime, provider },
    }))
  }, [])

  const updateRole = useCallback((role: AgentRole) => {
    setSettings((prev) => ({
      ...prev,
      runtime: { ...prev.runtime, role },
    }))
  }, [])

  const updateAutonomy = useCallback((updates: Partial<CockpitSettings['runtime']['autonomy']>) => {
    setSettings((prev) => ({
      ...prev,
      runtime: {
        ...prev.runtime,
        autonomy: { ...prev.runtime.autonomy, ...updates },
      },
    }))
  }, [])

  const updateAutonomyLevel = useCallback((level: AutonomyLevel) => {
    setSettings((prev) => ({
      ...prev,
      runtime: {
        ...prev.runtime,
        autonomy: { ...prev.runtime.autonomy, level },
      },
    }))
  }, [])

  const updatePersistence = useCallback((persistence: PersistenceLevel) => {
    setSettings((prev) => ({
      ...prev,
      runtime: {
        ...prev.runtime,
        autonomy: { ...prev.runtime.autonomy, persistence },
      },
    }))
  }, [])

  // Capabilities updates
  const updateSkills = useCallback((updates: Partial<CockpitSettings['capabilities']['skills']>) => {
    setSettings((prev) => ({
      ...prev,
      capabilities: {
        ...prev.capabilities,
        skills: { ...prev.capabilities.skills, ...updates },
      },
    }))
  }, [])

  const toggleSkill = useCallback((skillId: string) => {
    setSettings((prev) => ({
      ...prev,
      capabilities: {
        ...prev.capabilities,
        skills: {
          ...prev.capabilities.skills,
          sets: prev.capabilities.skills.sets.map((skill) =>
            skill.id === skillId ? { ...skill, enabled: !skill.enabled } : skill
          ),
        },
      },
    }))
  }, [])

  const updateSystemAccess = useCallback((updates: Partial<SystemAccess>) => {
    setSettings((prev) => ({
      ...prev,
      capabilities: {
        ...prev.capabilities,
        systemAccess: { ...prev.capabilities.systemAccess, ...updates },
      },
    }))
  }, [])

  // Culture updates
  const updateCulture = useCallback((updates: Partial<CultureConfig>) => {
    setSettings((prev) => ({
      ...prev,
      culture: { ...prev.culture, ...updates },
    }))
  }, [])

  // Actions
  const saveSettings = useCallback(() => {
    postMessage({
      type: 'cockpit:settings:save',
      payload: { settings },
    })
    setOriginalSettings(settings)
  }, [postMessage, settings])

  const previewCliArgs = useCallback(() => {
    postMessage({
      type: 'cockpit:settings:preview',
      payload: { settings },
    })
  }, [postMessage, settings])

  return {
    settings,
    isLoading,
    availableProviders,
    availableSkills,
    updateRuntime,
    updateProvider,
    updateRole,
    updateAutonomy,
    updateAutonomyLevel,
    updatePersistence,
    updateSkills,
    toggleSkill,
    updateSystemAccess,
    updateCulture,
    saveSettings,
    previewCliArgs,
    hasChanges,
  }
}
