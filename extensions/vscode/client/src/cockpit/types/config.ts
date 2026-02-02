/**
 * Cockpit Settings Configuration Types
 * Defines the structure for Agent Runtime and Capabilities configuration
 */

/**
 * Agent Provider (Kernel) - Backend service driving the agent
 */
export type AgentProvider = 'kimi' | 'vertex-ai' | 'openai' | 'anthropic' | 'local'

/**
 * Agent Role (Persona) - The role/persona of the agent
 */
export type AgentRole = 
  | 'principal-architect'
  | 'senior-engineer'
  | 'qa-specialist'
  | 'devops-engineer'
  | 'security-analyst'
  | 'product-manager'
  | 'default'

/**
 * Autonomy Level - Human-in-the-loop configuration
 */
export type AutonomyLevel = 'yolo' | 'step-by-step' | 'full-manual'

/**
 * Persistence Level - Execution time and permission scope
 */
export type PersistenceLevel = 'unlimited' | 'session' | 'task'

/**
 * Skill Set - Available skill packages
 */
export interface SkillSet {
  id: string
  name: string
  description: string
  enabled: boolean
  path?: string
  version?: string
}

/**
 * System Access - Bash-as-Tool configuration
 */
export interface SystemAccess {
  enabled: boolean
  allowNetwork: boolean
  allowFileSystem: boolean
  allowSystemCommands: boolean
  restrictedCommands: string[]
}

/**
 * Agent Runtime Configuration
 */
export interface AgentRuntimeConfig {
  provider: AgentProvider
  role: AgentRole
  autonomy: {
    level: AutonomyLevel
    persistence: PersistenceLevel
  }
}

/**
 * Capabilities Configuration
 */
export interface CapabilitiesConfig {
  skills: {
    directory: string
    sets: SkillSet[]
  }
  systemAccess: SystemAccess
}

/**
 * Culture Configuration
 */
export interface CultureConfig {
  language: 'en' | 'zh' | 'auto'
  tone: 'professional' | 'casual' | 'technical'
  responseStyle: 'concise' | 'detailed' | 'balanced'
}

/**
 * Complete Cockpit Settings
 */
export interface CockpitSettings {
  runtime: AgentRuntimeConfig
  capabilities: CapabilitiesConfig
  culture: CultureConfig
}

/**
 * Default settings
 */
export const DEFAULT_COCKPIT_SETTINGS: CockpitSettings = {
  runtime: {
    provider: 'kimi',
    role: 'senior-engineer',
    autonomy: {
      level: 'yolo',
      persistence: 'unlimited',
    },
  },
  capabilities: {
    skills: {
      directory: '~/.monoco/skills',
      sets: [],
    },
    systemAccess: {
      enabled: true,
      allowNetwork: true,
      allowFileSystem: true,
      allowSystemCommands: true,
      restrictedCommands: ['rm -rf /', 'dd', 'mkfs'],
    },
  },
  culture: {
    language: 'auto',
    tone: 'professional',
    responseStyle: 'balanced',
  },
}

/**
 * Provider metadata for UI display
 */
export const PROVIDER_METADATA: Record<AgentProvider, { name: string; description: string; icon: string }> = {
  'kimi': {
    name: 'Kimi',
    description: 'Moonshot AI Kimi - Advanced reasoning and coding',
    icon: '🌙',
  },
  'vertex-ai': {
    name: 'Vertex AI',
    description: 'Google Cloud Vertex AI - Enterprise-grade',
    icon: '☁️',
  },
  'openai': {
    name: 'OpenAI',
    description: 'OpenAI GPT - General purpose AI',
    icon: '🤖',
  },
  'anthropic': {
    name: 'Anthropic',
    description: 'Claude - Safety-focused AI',
    icon: '🧠',
  },
  'local': {
    name: 'Local',
    description: 'Local LLM - Privacy-first on-device',
    icon: '🏠',
  },
}

/**
 * Role metadata for UI display
 */
export const ROLE_METADATA: Record<AgentRole, { name: string; description: string; icon: string }> = {
  'principal-architect': {
    name: 'Principal Architect',
    description: 'High-level design, system architecture, technical decisions',
    icon: '🏛️',
  },
  'senior-engineer': {
    name: 'Senior Engineer',
    description: 'Full-stack development, code review, best practices',
    icon: '👨‍💻',
  },
  'qa-specialist': {
    name: 'QA Specialist',
    description: 'Testing, quality assurance, bug hunting',
    icon: '🐞',
  },
  'devops-engineer': {
    name: 'DevOps Engineer',
    description: 'CI/CD, infrastructure, deployment automation',
    icon: '⚙️',
  },
  'security-analyst': {
    name: 'Security Analyst',
    description: 'Security review, vulnerability assessment',
    icon: '🔒',
  },
  'product-manager': {
    name: 'Product Manager',
    description: 'Requirements, prioritization, user stories',
    icon: '📋',
  },
  'default': {
    name: 'Default',
    description: 'General-purpose agent behavior',
    icon: '🎯',
  },
}

/**
 * Autonomy level metadata
 */
export const AUTONOMY_METADATA: Record<AutonomyLevel, { name: string; description: string }> = {
  'yolo': {
    name: 'YOLO Mode',
    description: 'Auto-approve all actions. Maximum efficiency.',
  },
  'step-by-step': {
    name: 'Step-by-Step',
    description: 'Confirm each significant action before execution.',
  },
  'full-manual': {
    name: 'Full Manual',
    description: 'Detailed approval for every operation.',
  },
}

/**
 * Persistence level metadata
 */
export const PERSISTENCE_METADATA: Record<PersistenceLevel, { name: string; description: string }> = {
  'unlimited': {
    name: 'Unlimited',
    description: 'No time limits. Full execution scope.',
  },
  'session': {
    name: 'Session',
    description: 'Limited to current IDE session.',
  },
  'task': {
    name: 'Task',
    description: 'Limited to single task completion.',
  },
}
