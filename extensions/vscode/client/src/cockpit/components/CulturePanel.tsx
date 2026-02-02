/**
 * Culture Configuration Panel
 * Configure Language, Tone, and Response Style
 */

import React from 'react'
import {
  VSCodeDropdown,
  VSCodeOption,
  VSCodeLabel,
  VSCodeRadioGroup,
  VSCodeRadio,
} from '@vscode/webview-ui-toolkit/react'
import { CultureConfig } from '../types/config'

interface CulturePanelProps {
  culture: CultureConfig
  onCultureChange: (updates: Partial<CultureConfig>) => void
}

const LANGUAGES = [
  { value: 'auto', label: '🌐 Auto-detect', description: 'Automatically detect from context' },
  { value: 'en', label: '🇺🇸 English', description: 'US English' },
  { value: 'zh', label: '🇨🇳 中文', description: 'Simplified Chinese' },
]

const TONES = [
  { value: 'professional', label: 'Professional', description: 'Formal, business-appropriate communication' },
  { value: 'technical', label: 'Technical', description: 'Precise, jargon-friendly, detailed' },
  { value: 'casual', label: 'Casual', description: 'Relaxed, conversational style' },
]

const RESPONSE_STYLES = [
  { value: 'concise', label: 'Concise', description: 'Brief, to-the-point responses' },
  { value: 'balanced', label: 'Balanced', description: 'Moderate detail with clarity' },
  { value: 'detailed', label: 'Detailed', description: 'Comprehensive, thorough explanations' },
]

export const CulturePanel: React.FC<CulturePanelProps> = ({
  culture,
  onCultureChange,
}) => {
  return (
    <div className="culture-panel">
      <section className="config-section">
        <h3 className="section-title">
          <span className="icon">🌍</span>
          Language & Localization
        </h3>
        <p className="section-description">
          Configure communication language and cultural preferences.
        </p>

        <div className="form-group">
          <VSCodeLabel htmlFor="language-select">Language</VSCodeLabel>
          <VSCodeDropdown
            id="language-select"
            value={culture.language}
            onChange={(e: any) => onCultureChange({ language: e.target.value })}
          >
            {LANGUAGES.map((lang) => (
              <VSCodeOption key={lang.value} value={lang.value}>
                {lang.label}
              </VSCodeOption>
            ))}
          </VSCodeDropdown>
          <p className="field-hint">
            {LANGUAGES.find((l) => l.value === culture.language)?.description}
          </p>
        </div>
      </section>

      <section className="config-section">
        <h3 className="section-title">
          <span className="icon">🎭</span>
          Communication Style
        </h3>
        <p className="section-description">
          Define the tone and style of agent responses.
        </p>

        <div className="form-group">
          <VSCodeLabel>Tone</VSCodeLabel>
          <VSCodeRadioGroup
            value={culture.tone}
            onChange={(e: any) => onCultureChange({ tone: e.target.value })}
          >
            {TONES.map((tone) => (
              <VSCodeRadio key={tone.value} value={tone.value}>
                <div className="radio-content">
                  <span className="radio-label">{tone.label}</span>
                  <span className="radio-description">{tone.description}</span>
                </div>
              </VSCodeRadio>
            ))}
          </VSCodeRadioGroup>
        </div>

        <div className="form-group">
          <VSCodeLabel>Response Style</VSCodeLabel>
          <VSCodeRadioGroup
            value={culture.responseStyle}
            onChange={(e: any) => onCultureChange({ responseStyle: e.target.value })}
          >
            {RESPONSE_STYLES.map((style) => (
              <VSCodeRadio key={style.value} value={style.value}>
                <div className="radio-content">
                  <span className="radio-label">{style.label}</span>
                  <span className="radio-description">{style.description}</span>
                </div>
              </VSCodeRadio>
            ))}
          </VSCodeRadioGroup>
        </div>
      </section>

      <section className="config-section preview-section">
        <h3 className="section-title">
          <span className="icon">👁️</span>
          Preview
        </h3>
        <div className="preview-card">
          <div className="preview-header">
            <span className="preview-icon">🤖</span>
            <span className="preview-title">Agent Response Preview</span>
          </div>
          <div className="preview-content">
            <p className="preview-text">
              {culture.tone === 'professional' && "I'll proceed with implementing the requested feature. The solution will be delivered according to best practices."}
              {culture.tone === 'technical' && "Implementing feature with TypeScript/React. Will use functional components with hooks for state management."}
              {culture.tone === 'casual' && "Sure thing! I'll get this feature built for you. Should be straightforward!"}
            </p>
            <div className="preview-meta">
              <span className="preview-tag">{culture.language}</span>
              <span className="preview-tag">{culture.tone}</span>
              <span className="preview-tag">{culture.responseStyle}</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
