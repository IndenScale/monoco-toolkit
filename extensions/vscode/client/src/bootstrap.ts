import * as vscode from "vscode";
import * as cp from "child_process";
import * as os from "os";
import * as path from "path";

// Export system wrapper for testing
export const sys = {
  exec: cp.exec,
};

export async function checkAndBootstrap() {
  // 1. Check if monoco is already available
  // Use --help because older versions of monoco (typer default) don't support --version
  const config = vscode.workspace.getConfiguration("monoco");
  const executable = config.get<string>("executablePath") || "monoco";
  
  if (await isCommandAvailable(executable, "--help")) {
    return;
  }

  // If default "monoco" failed, try ~/.local/bin/monoco (uv tool default)
  if (executable === "monoco") {
      const home = os.homedir();
      const uvPath = path.join(home, ".local", "bin", "monoco");
      if (await isCommandAvailable(uvPath, "--help")) {
          return;
      }
  }

  // 2. Monoco not found. Check if uv is available.
  const hasUv = await isCommandAvailable("uv");

  if (hasUv) {
    // Scenario A: uv exists, just install toolkit
    const selection = await vscode.window.showInformationMessage(
      "Monoco Toolkit CLI is missing. Install it via uv?",
      "Install",
      "Cancel"
    );
    if (selection === "Install") {
      await installMonocoToolkit();
    }
  } else {
    // Scenario B: uv missing. Install uv first.
    const selection = await vscode.window.showWarningMessage(
      "Monoco Toolkit requires 'uv' (Fast Python Pkg Mgr). Install 'uv' + Toolkit?",
      "Install All",
      "Cancel"
    );
    if (selection === "Install All") {
      await installUvAndToolkit();
    }
  }
}

async function isCommandAvailable(
  cmd: string,
  flag: string = "--version"
): Promise<boolean> {
  return new Promise((resolve) => {
    // use 'command -v' on unix, 'where' on windows, or just run --version
    // --version is safest for most CLIs
    sys.exec(`${cmd} ${flag}`, (err) => {
      if (err) {
        console.log(
          `[Monoco] Command check failed for '${cmd}': ${err.message}`
        );
        console.log(`[Monoco] PATH: ${process.env.PATH}`);
      }
      resolve(!err);
    });
  });
}

async function installMonocoToolkit() {
  const terminal = getInstallerTerminal();
  terminal.show();
  terminal.sendText("uv tool install monoco-toolkit");
}

async function installUvAndToolkit() {
  const terminal = getInstallerTerminal();
  terminal.show();

  if (process.platform === "win32") {
    // Windows: Install uv then Monoco
    // We use ; to separate commands in PS or && if acceptable, but sendText implies separate lines or chained.
    // Let's chain them.
    terminal.sendText(
      'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
    );
    // We assume uv is added to path or we try to use it. Windows environment update in same terminal is hard.
    // It's safer to tell users.
    terminal.sendText('Write-Host "Installing Monoco Toolkit..."');
    // Try to assume default install path or just run it hoping alias works (often requires restart)
    terminal.sendText("uv tool install monoco-toolkit");
  } else {
    // macOS / Linux
    // 1. Install uv
    terminal.sendText("curl -LsSf https://astral.sh/uv/install.sh | sh");

    // 2. Install Monoco using the likely path of uv (since PATH needs shell restart)
    // uv default install location: ~/.local/bin/uv (or $HOME/.cargo/bin sometimes for older scripts, but uv is standalone now)
    // The script outputs where it installed.
    // We try to run explicitly from ~/.local/bin/uv
    const installCmd = `~/.local/bin/uv tool install monoco-toolkit`;

    terminal.sendText(`echo "Attempting to install Monoco Toolkit..."`);
    // We try the direct path, if that fails, we fallback to requesting user restart.
    terminal.sendText(
      `${installCmd} || echo "Please restart your terminal to load 'uv', then run: uv tool install monoco-toolkit"`
    );
  }
}

function getInstallerTerminal(): vscode.Terminal {
  let terminal = vscode.window.terminals.find(
    (t) => t.name === "Monoco Installer"
  );
  if (!terminal) {
    terminal = vscode.window.createTerminal({
      name: "Monoco Installer",
      iconPath: new vscode.ThemeIcon("cloud-download"),
    });
  }
  return terminal;
}
