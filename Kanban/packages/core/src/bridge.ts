/**
 * VsCodeMessenger provides a bridge between the Webview and the VS Code extension.
 */
export class VsCodeMessenger {
  private vscode: any | undefined;
  private _isVsCode: boolean = false;

  constructor() {
    if (typeof window !== "undefined") {
      // @ts-ignore
      if (typeof acquireVsCodeApi !== "undefined") {
        // @ts-ignore
        this.vscode = acquireVsCodeApi();
        this._isVsCode = true;
      }
    }
  }

  /**
   * Returns true if the current environment is a VS Code webview.
   */
  public get isVsCode(): boolean {
    return this._isVsCode;
  }

  /**
   * Send a message to the VS Code extension.
   */
  public postMessage(type: string, payload?: any) {
    if (this._isVsCode && this.vscode) {
      this.vscode.postMessage({ type, ...payload });
    } else {
      console.debug(`[VsCodeMessenger] postMessage(type=${type})`, payload);
    }
  }

  /**
   * Listen for messages from the VS Code extension.
   */
  public onMessage(type: string, callback: (payload: any) => void): () => void {
    if (typeof window === "undefined") return () => {};

    const handler = (event: MessageEvent) => {
      const message = event.data;
      if (message && message.type === type) {
        callback(message);
      }
    };

    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }

  /**
   * Get the current state from VS Code.
   */
  public getState(): any {
    return this.vscode?.getState();
  }

  /**
   * Set the current state in VS Code (survives when webview is hidden).
   */
  public setState(state: any) {
    this.vscode?.setState(state);
  }
}

export const vscodeMessenger = new VsCodeMessenger();
