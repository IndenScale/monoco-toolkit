/**
 * Message types for webview <-> extension communication
 */
/**
 * Type guard for webview messages
 */
export function isWebviewMessage(message) {
  return message && typeof message.type === 'string'
}
/**
 * Type guard for extension messages
 */
export function isExtensionMessage(message) {
  return message && typeof message.type === 'string'
}
