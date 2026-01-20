import { StateManager } from '../state/StateManager'
import { VSCodeBridge } from '../services/VSCodeBridge'

/**
 * Issue creation form component
 */
export class CreateForm {
  private titleInput: HTMLInputElement
  private typeSelect: HTMLSelectElement
  private parentSelect: HTMLSelectElement
  private projectSelect: HTMLSelectElement
  private submitBtn: HTMLButtonElement

  constructor(
    _container: HTMLElement,
    private stateManager: StateManager,
    private bridge: VSCodeBridge
  ) {
    // Get form elements
    this.titleInput = document.getElementById('create-title') as HTMLInputElement
    this.typeSelect = document.getElementById('create-type') as HTMLSelectElement
    this.parentSelect = document.getElementById('create-parent') as HTMLSelectElement
    this.projectSelect = document.getElementById('create-project') as HTMLSelectElement
    this.submitBtn = document.getElementById('btn-submit-create') as HTMLButtonElement

    // Setup event listeners
    this.setupEventListeners()
  }

  /**
   * Setup event listeners
   */
  private setupEventListeners() {
    // Submit button
    this.submitBtn?.addEventListener('click', async () => {
      await this.submit()
    })

    // Drag & drop for parent selection
    if (this.parentSelect) {
      this.parentSelect.addEventListener('dragover', (e) => {
        e.preventDefault()
        e.dataTransfer!.dropEffect = 'copy'
        this.parentSelect.style.borderColor = 'var(--vscode-focusBorder)'
      })

      this.parentSelect.addEventListener('dragleave', () => {
        this.parentSelect.style.borderColor = ''
      })

      this.parentSelect.addEventListener('drop', (e) => {
        e.preventDefault()
        this.parentSelect.style.borderColor = ''
        const raw = e.dataTransfer!.getData('application/monoco-issue')
        if (raw) {
          try {
            const droppedIssue = JSON.parse(raw)
            if (droppedIssue && droppedIssue.id) {
              // Add option if missing
              let optionExists = false
              for (let i = 0; i < this.parentSelect.options.length; i++) {
                if (this.parentSelect.options[i].value === droppedIssue.id) {
                  optionExists = true
                  break
                }
              }
              if (!optionExists) {
                const opt = document.createElement('option')
                opt.value = droppedIssue.id
                opt.textContent = `${droppedIssue.id}: ${droppedIssue.title}`
                this.parentSelect.appendChild(opt)
              }
              this.parentSelect.value = droppedIssue.id
            }
          } catch (e) {
            console.error('Drop failed', e)
          }
        }
      })
    }
  }

  /**
   * Open create flow with pre-filled values
   */
  open(type: string = 'feature', parentId?: string) {
    const state = this.stateManager.getState()

    if (!state.selectedProjectId) {
      console.warn('No project selected')
      return
    }

    // Pre-fill form
    this.titleInput.value = ''
    this.typeSelect.value = type
    this.projectSelect.value = state.selectedProjectId

    // Populate parent options
    this.populateParentOptions(state.selectedProjectId, parentId)

    // Focus title input
    this.titleInput.focus()
  }

  /**
   * Populate parent options
   */
  private async populateParentOptions(_currentProjectId: string, preselectedId?: string) {
    const state = this.stateManager.getState()
    const select = this.parentSelect

    select.innerHTML = '<option value="">(None)</option>'
    select.disabled = true

    try {
      const epics: any[] = []

      // Current project epics
      const currentEpics = state.issues
        .filter((i) => i.type === 'epic')
        .map((e) => ({ ...e, group: 'Current Project' }))
      epics.push(...currentEpics)

      // All epics/archs across projects
      const allRoots = state.issues
        .filter((i) => (i.type as string) === 'epic' || (i.type as string) === 'arch')
        .map((e) => {
          const p = state.projects.find((proj) => proj.id === e.project_id)
          return { ...e, group: p ? `Project: ${p.name}` : 'Other' }
        })
      epics.push(...allRoots)

      // Group by project
      const groups: Record<string, any[]> = {}
      epics.forEach((e) => {
        if (!groups[e.group]) {
          groups[e.group] = []
        }
        groups[e.group].push(e)
      })

      // Sort groups
      const groupNames = Object.keys(groups).sort((a, b) => {
        if (a === 'Current Project') {
          return -1
        }
        if (b === 'Current Project') {
          return 1
        }
        return a.localeCompare(b)
      })

      // Render options
      groupNames.forEach((g) => {
        const optgroup = document.createElement('optgroup')
        optgroup.label = g
        groups[g].forEach((e) => {
          const opt = document.createElement('option')
          opt.value = e.id
          opt.textContent = `${e.id}: ${e.title}`
          if (e.id === preselectedId) {
            opt.selected = true
          }
          optgroup.appendChild(opt)
        })
        select.appendChild(optgroup)
      })

      // Add preselected if not found
      if (preselectedId && !Array.from(select.options).some((o) => o.value === preselectedId)) {
        const opt = document.createElement('option')
        opt.value = preselectedId
        opt.textContent = `${preselectedId} (Unknown)`
        opt.selected = true
        select.appendChild(opt)
      }
    } catch (e) {
      console.warn('Failed to populate parents', e)
    } finally {
      select.disabled = false
    }
  }

  /**
   * Submit the form
   */
  private async submit() {
    const title = this.titleInput.value.trim()
    if (!title) {
      return
    }

    const type = this.typeSelect.value
    const parent = this.parentSelect.value.trim() || undefined

    this.bridge.createIssue({
      title,
      type: type.toLowerCase(),
      parent,
    })

    // Reset form
    this.titleInput.value = ''
  }
}
