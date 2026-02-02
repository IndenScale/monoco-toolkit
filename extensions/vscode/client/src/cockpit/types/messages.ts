/**
 * Message types for Cockpit Settings Webview communication
 */

import { CockpitSettings } from './config'

// Extension -> Webview messages
export interface ExtensionMessageMap {
  'cockpit:settings:loaded': {
    settings: CockpitSettings
    availableProviders: string[]
    availableSkills: Array<{ id: string; name: string; description: string }>
  }
  'cockpit:settings:saved': {
    success: boolean
    error?: string
  }
  'cockpit:cli:preview': {
    args: string[]
  }
}

// Webview -> Extension messages
export interface WebviewMessageMap {
  'cockpit:settings:load': {}
  'cockpit:settings:save': {
    settings: CockpitSettings
  }
  'cockpit:settings:preview': {
    settings: CockpitSettings
  }
  'cockpit:skills:scan': {
    directory: string
  }
  'cockpit:ready': {}
}

export type ExtensionMessageType = keyof ExtensionMessageMap
export type WebviewMessageType = keyof WebviewMessageMap

export interface ExtensionMessage<T extends ExtensionMessageType = ExtensionMessageType> {
  type: T
  payload: ExtensionMessageMap[T]
}

export interface WebviewMessage<T extends WebviewMessageType = WebviewMessageType> {
  type: T
  payload: WebviewMessageMap[T]
}
