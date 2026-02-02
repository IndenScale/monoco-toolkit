/**
 * Cockpit Settings Webview Entry Point
 * React application for Monoco Cockpit configuration
 */

import React from 'react'
import { createRoot } from 'react-dom/client'
import { CockpitApp } from './views/CockpitApp'
import './styles/cockpit.css'

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('root')
  if (!container) {
    console.error('[Cockpit] Root element not found')
    return
  }

  const root = createRoot(container)
  root.render(
    <React.StrictMode>
      <CockpitApp />
    </React.StrictMode>
  )

  console.log('[Cockpit] React application mounted')
})
