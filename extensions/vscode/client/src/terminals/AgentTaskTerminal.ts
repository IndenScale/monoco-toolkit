import * as vscode from "vscode";
import * as cp from "child_process";
import { resolveMonocoExecutable } from "../bootstrap";

export class AgentTaskTerminal implements vscode.Pseudoterminal {
  private writeEmitter = new vscode.EventEmitter<string>();
  private closeEmitter = new vscode.EventEmitter<number>();
  private process?: cp.ChildProcess;
  private isClosed = false;

  onDidWrite: vscode.Event<string> = this.writeEmitter.event;
  onDidClose: vscode.Event<number> = this.closeEmitter.event;

  constructor(
    private readonly actionName: string,
    private readonly targetFile?: string,
    private readonly instruction?: string,
    private readonly cwd?: string,
  ) {}

  async open(
    _initialDimensions: vscode.TerminalDimensions | undefined,
  ): Promise<void> {
    this.writeEmitter.fire(`Starting Agent Action: ${this.actionName}\r\n`);

    try {
      const executable = await resolveMonocoExecutable();
      const args = ["agent", "run", this.actionName];

      if (this.targetFile) {
        args.push(this.targetFile);
      }
      if (this.instruction) {
        args.push("--instruction", this.instruction);
      }

      // Add --json if we wanted structured output, but for terminal we want human readable
      // args.push("--json");

      this.writeEmitter.fire(
        `Executing: ${executable} ${args.join(" ")}\r\n\r\n`,
      );

      this.process = cp.spawn(executable, args, {
        cwd: this.cwd || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
        env: process.env,
        shell: false, // Direct spawn
      });

      this.process.stdout?.on("data", (data) => {
        this.write(data.toString());
      });

      this.process.stderr?.on("data", (data) => {
        this.write(data.toString());
      });

      this.process.on("error", (error) => {
        this.writeEmitter.fire(
          `\r\nError launching process: ${error.message}\r\n`,
        );
        this.closeEmitter.fire(1);
      });

      this.process.on("close", (code) => {
        this.writeEmitter.fire(`\r\nProcess exited with code ${code}\r\n`);
        this.closeEmitter.fire(code || 0);
      });
    } catch (e: any) {
      this.writeEmitter.fire(`\r\nFailed to start agent: ${e.message}\r\n`);
      this.closeEmitter.fire(1);
    }
  }

  close(): void {
    if (this.isClosed) {
      return;
    }
    this.isClosed = true;
    if (this.process) {
      this.process.kill();
    }
  }

  handleInput(data: string): void {
    if (this.process && !this.process.killed && this.process.stdin) {
      this.process.stdin.write(data);
    }
  }

  private write(data: string) {
    // Normalize line endings to \r\n for terminal
    const normalized = data.replace(/\n/g, "\r\n");
    this.writeEmitter.fire(normalized);
  }
}
