import { IssueIndex } from '@shared/types/Issue'
import { Project } from '@shared/types/Project'

/**
 * Application state structure
 */
export interface AppState {
  issues: IssueIndex[]
  projects: Project[]
  selectedProjectId: string | null
  expandedIds: Set<string>
  searchQuery: string
  filters: {
    status: string[]
    stage: string[]
    tags: {
      include: string[]
      exclude: string[]
      nice: string[]
    }
  }
  workspaceState: {
    last_active_project_id?: string
  }
  settings: {
    agents: {
      research: string
      implementation: string
      review: string
      default: string
    }
    ui: {
      displayId: boolean
    }
  }
  availableProviders: string[]
}

/**
 * State change listener
 */
type StateListener = (state: Readonly<AppState>) => void

/**
 * Centralized state manager for the webview
 * Implements observable pattern for reactive UI updates
 */
export class StateManager {
  private state: AppState = {
    issues: [],
    projects: [],
    selectedProjectId: null,
    expandedIds: new Set(),
    searchQuery: '',
    filters: {
      status: [],
      stage: [],
      tags: { include: [], exclude: [], nice: [] },
    },
    workspaceState: {},
    settings: {
      agents: {
        research: 'gemini',
        implementation: 'gemini',
        review: 'gemini',
        default: 'gemini',
      },
      ui: {
        displayId: true,
      },
    },
    availableProviders: [],
  }

  private listeners: Set<StateListener> = new Set()

  /**
   * Get current state (readonly)
   */
  getState(): Readonly<AppState> {
    return this.state
  }

  /**
   * Update state with partial changes
   */
  setState(partial: Partial<AppState>) {
    this.state = { ...this.state, ...partial }
    this.notify()
  }

  /**
   * Update a specific field in state
   */
  updateField<K extends keyof AppState>(key: K, value: AppState[K]) {
    this.state[key] = value
    this.notify()
  }

  /**
   * Toggle expansion state for an issue
   */
  toggleExpanded(issueId: string) {
    const expandedIds = new Set(this.state.expandedIds)
    if (expandedIds.has(issueId)) {
      expandedIds.delete(issueId)
    } else {
      expandedIds.add(issueId)
    }
    this.setState({ expandedIds })
  }

  /**
   * Subscribe to state changes
   * @returns Unsubscribe function
   */
  subscribe(listener: StateListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  /**
   * Notify all listeners of state change
   */
  private notify() {
    this.listeners.forEach((listener) => listener(this.state))
  }

  /**
   * Load state from localStorage
   */
  loadFromStorage() {
    try {
      const saved = localStorage.getItem('monocoState')
      if (saved) {
        const parsed = JSON.parse(saved)

        // Merge settings with defaults to handle legacy versions
        const settings = {
          ...this.state.settings,
          ...(parsed.settings || {}),
          agents: {
            ...this.state.settings.agents,
            ...(parsed.settings?.agents || {}),
          },
          ui: {
            ...this.state.settings.ui,
            ...(parsed.settings?.ui || {}),
          },
        }

        this.setState({
          settings,
          expandedIds: new Set(parsed.expandedIds || []),
        })
      }
    } catch (e) {
      console.error('Failed to load state from storage', e)
    }
  }

  /**
   * Save state to localStorage
   */
  saveToStorage() {
    try {
      const toSave = {
        settings: this.state.settings,
        expandedIds: Array.from(this.state.expandedIds),
      }
      localStorage.setItem('monocoState', JSON.stringify(toSave))
    } catch (e) {
      console.error('Failed to save state to storage', e)
    }
  }
}
