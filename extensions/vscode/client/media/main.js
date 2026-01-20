// @ts-check

// This script will be run within the webview itself
// It cannot access the main VS Code APIs directly.
;(function () {
  const vscode = acquireVsCodeApi()

  const oldState = vscode.getState() || { colors: [] }

  /** @type {Array<{ value: string }>} */
  let colors = oldState.colors

  updateColorList(colors)

  document.querySelector('.add-color-button').addEventListener('click', () => {
    addColor()
  })

  // Handle messages sent from the extension to the webview
  window.addEventListener('message', (event) => {
    const message = event.data // The json data that the extension sent
    switch (message.type) {
      case 'addColor': {
        addColor()
        break
      }
      case 'clearColors': {
        colors = []
        updateColorList(colors)
        break
      }
    }
  })

  function addColor() {
    colors.push({ value: getNewCalicoColor() })
    updateColorList(colors)
  }

  function updateColorList(/** @type {any[]} */ colors) {
    const ul = document.querySelector('.color-list')
    ul.textContent = ''
    for (const color of colors) {
      const li = document.createElement('li')
      li.className = 'color-entry'

      const colorPreview = document.createElement('div')
      colorPreview.className = 'color-box'
      colorPreview.style.backgroundColor = color.value
      colorPreview.addEventListener('click', () => {
        onColorClicked(color.value)
      })
      li.appendChild(colorPreview)

      const input = document.createElement('span')
      input.textContent = color.value
      li.appendChild(input)

      ul.appendChild(li)
    }

    // Update the saved state
    vscode.setState({ colors: colors })
  }

  /**
   * @param {string} color
   */
  function onColorClicked(color) {
    vscode.postMessage({ type: 'colorSelected', value: color })
  }

  function getNewCalicoColor() {
    const colors = ['#007acc', '#ffffff', '#ff0000', '#00ff00', '#0000ff']
    return colors[Math.floor(Math.random() * colors.length)]
  }
})()
