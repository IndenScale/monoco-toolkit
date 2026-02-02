/**
 * Tests for Cockpit Configuration Types
 */

import * as assert from 'assert'
import {
  DEFAULT_COCKPIT_SETTINGS,
  PROVIDER_METADATA,
  ROLE_METADATA,
  AUTONOMY_METADATA,
  PERSISTENCE_METADATA,
} from '../../../cockpit/types/config'

suite('Cockpit Config Types', () => {
  test('DEFAULT_COCKPIT_SETTINGS has correct structure', () => {
    assert.ok(DEFAULT_COCKPIT_SETTINGS.runtime)
    assert.ok(DEFAULT_COCKPIT_SETTINGS.capabilities)
    assert.ok(DEFAULT_COCKPIT_SETTINGS.culture)

    // Runtime
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.runtime.provider, 'kimi')
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.runtime.role, 'senior-engineer')
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.runtime.autonomy.level, 'yolo')
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.runtime.autonomy.persistence, 'unlimited')

    // Capabilities
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.enabled, true)
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.allowNetwork, true)
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.allowFileSystem, true)
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.capabilities.systemAccess.allowSystemCommands, true)

    // Culture
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.culture.language, 'auto')
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.culture.tone, 'professional')
    assert.strictEqual(DEFAULT_COCKPIT_SETTINGS.culture.responseStyle, 'balanced')
  })

  test('PROVIDER_METADATA contains all providers', () => {
    assert.ok(PROVIDER_METADATA['kimi'])
    assert.ok(PROVIDER_METADATA['vertex-ai'])
    assert.ok(PROVIDER_METADATA['openai'])
    assert.ok(PROVIDER_METADATA['anthropic'])
    assert.ok(PROVIDER_METADATA['local'])

    // Check structure
    assert.ok(PROVIDER_METADATA['kimi'].name)
    assert.ok(PROVIDER_METADATA['kimi'].description)
    assert.ok(PROVIDER_METADATA['kimi'].icon)
  })

  test('ROLE_METADATA contains all roles', () => {
    assert.ok(ROLE_METADATA['principal-architect'])
    assert.ok(ROLE_METADATA['senior-engineer'])
    assert.ok(ROLE_METADATA['qa-specialist'])
    assert.ok(ROLE_METADATA['devops-engineer'])
    assert.ok(ROLE_METADATA['security-analyst'])
    assert.ok(ROLE_METADATA['product-manager'])
    assert.ok(ROLE_METADATA['default'])

    // Check structure
    assert.ok(ROLE_METADATA['senior-engineer'].name)
    assert.ok(ROLE_METADATA['senior-engineer'].description)
    assert.ok(ROLE_METADATA['senior-engineer'].icon)
  })

  test('AUTONOMY_METADATA contains all levels', () => {
    assert.ok(AUTONOMY_METADATA['yolo'])
    assert.ok(AUTONOMY_METADATA['step-by-step'])
    assert.ok(AUTONOMY_METADATA['full-manual'])

    assert.strictEqual(AUTONOMY_METADATA['yolo'].name, 'YOLO Mode')
    assert.ok(AUTONOMY_METADATA['yolo'].description)
  })

  test('PERSISTENCE_METADATA contains all levels', () => {
    assert.ok(PERSISTENCE_METADATA['unlimited'])
    assert.ok(PERSISTENCE_METADATA['session'])
    assert.ok(PERSISTENCE_METADATA['task'])

    assert.strictEqual(PERSISTENCE_METADATA['unlimited'].name, 'Unlimited')
    assert.ok(PERSISTENCE_METADATA['unlimited'].description)
  })
})
