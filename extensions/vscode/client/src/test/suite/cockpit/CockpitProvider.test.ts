/**
 * Tests for CockpitProvider
 */

import * as assert from 'assert'
import * as vscode from 'vscode'
import { CockpitProvider } from '../../../cockpit/CockpitProvider'
import { DEFAULT_COCKPIT_SETTINGS, CockpitSettings } from '../../../cockpit/types/config'

suite('CockpitProvider', () => {
  let provider: CockpitProvider

  setup(() => {
    const extensionUri = vscode.Uri.file('/test/extension')
    provider = new CockpitProvider(extensionUri)
  })

  teardown(() => {
    provider.dispose()
  })

  test('provider is created successfully', () => {
    assert.ok(provider)
  })

  test('provider has correct view type', () => {
    assert.strictEqual(CockpitProvider.viewType, 'monoco.cockpitSettings')
  })

  test('DEFAULT_COCKPIT_SETTINGS can be used to create valid settings', () => {
    const settings: CockpitSettings = { ...DEFAULT_COCKPIT_SETTINGS }
    assert.ok(settings)
    assert.strictEqual(settings.runtime.provider, 'kimi')
  })

  test('settings can be modified while maintaining type safety', () => {
    const settings: CockpitSettings = {
      ...DEFAULT_COCKPIT_SETTINGS,
      runtime: {
        ...DEFAULT_COCKPIT_SETTINGS.runtime,
        provider: 'openai',
        role: 'principal-architect',
      },
    }

    assert.strictEqual(settings.runtime.provider, 'openai')
    assert.strictEqual(settings.runtime.role, 'principal-architect')
  })

  test('system access settings can be toggled', () => {
    const settings: CockpitSettings = {
      ...DEFAULT_COCKPIT_SETTINGS,
      capabilities: {
        ...DEFAULT_COCKPIT_SETTINGS.capabilities,
        systemAccess: {
          ...DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess,
          enabled: false,
          allowNetwork: false,
        },
      },
    }

    assert.strictEqual(settings.capabilities.systemAccess.enabled, false)
    assert.strictEqual(settings.capabilities.systemAccess.allowNetwork, false)
    assert.strictEqual(settings.capabilities.systemAccess.allowFileSystem, true) // unchanged
  })

  test('skills can be added to settings', () => {
    const settings: CockpitSettings = {
      ...DEFAULT_COCKPIT_SETTINGS,
      capabilities: {
        ...DEFAULT_COCKPIT_SETTINGS.capabilities,
        skills: {
          directory: '~/.monoco/skills',
          sets: [
            {
              id: 'test-skill',
              name: 'Test Skill',
              description: 'A test skill',
              enabled: true,
              version: '1.0.0',
            },
          ],
        },
      },
    }

    assert.strictEqual(settings.capabilities.skills.sets.length, 1)
    assert.strictEqual(settings.capabilities.skills.sets[0].id, 'test-skill')
    assert.strictEqual(settings.capabilities.skills.sets[0].enabled, true)
  })
})
