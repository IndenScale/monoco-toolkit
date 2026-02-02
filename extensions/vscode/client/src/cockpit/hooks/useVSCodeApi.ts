/**
 * React hook for VS Code Webview API
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import { ExtensionMessage, WebviewMessage, ExtensionMessageType } from '../types/messages'

export function useVSCodeApi() {
  const vscodeRef = useRef<any>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    // @ts-ignore - acquireVsCodeApi is injected by VS Code
    if (typeof acquireVsCodeApi === 'function') {
      // @ts-ignore
      vscodeRef.current = acquireVsCodeApi()
      setIsReady(true)
      
      // Notify extension that webview is ready
      vscodeRef.current.postMessage({
        type: 'cockpit:ready',
        payload: {},
      })
    }
  }, [])

  const postMessage = useCallback(<T extends WebviewMessage>(message: T) => {
    if (vscodeRef.current) {
      vscodeRef.current.postMessage(message)
    }
  }, [])

  const onMessage = useCallback(<T extends ExtensionMessageType>(
    type: T,
    handler: (payload: ExtensionMessage<T>['payload']) => void
  ) => {
    const listener = (event: MessageEvent) => {
      const message = event.data as ExtensionMessage
      if (message.type === type) {
        handler(message.payload as ExtensionMessage<T>['payload'])
      }
    }

    window.addEventListener('message', listener)
    return () => window.removeEventListener('message', listener)
  }, [])

  return {
    vscode: vscodeRef.current,
    isReady,
    postMessage,
    onMessage,
  }
}
