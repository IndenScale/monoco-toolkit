import * as assert from "assert";
import * as sinon from "sinon";
import * as vscode from "vscode";
import * as bootstrap from "../../bootstrap";

suite("Bootstrap Test Suite", () => {
  let sandbox: sinon.SinonSandbox;
  let showInfoStub: sinon.SinonStub;
  let showWarnStub: sinon.SinonStub;
  let execStub: sinon.SinonStub;
  let createTerminalStub: sinon.SinonStub;
  let terminalSendTextSpy: sinon.SinonSpy;
  let terminalShowSpy: sinon.SinonSpy;

  setup(() => {
    sandbox = sinon.createSandbox();
    showInfoStub = sandbox.stub(vscode.window, "showInformationMessage");
    showWarnStub = sandbox.stub(vscode.window, "showWarningMessage");
    // Stub the wrapper, not the native cp module
    execStub = sandbox.stub(bootstrap.sys, "exec");

    const terminalMock = {
      name: "Monoco Installer",
      sendText: sinon.spy(),
      show: sinon.spy(),
      exitStatus: undefined,
      processId: Promise.resolve(123),
      creationOptions: {},
      dispose: sinon.spy(),
      hide: sinon.spy(),
    } as unknown as vscode.Terminal;

    terminalSendTextSpy = terminalMock.sendText as sinon.SinonSpy;
    terminalShowSpy = terminalMock.show as sinon.SinonSpy;

    // Mock finding terminal or creating new one

    createTerminalStub = sandbox
      .stub(vscode.window, "createTerminal")
      .returns(terminalMock);
  });

  teardown(() => {
    sandbox.restore();
  });

  test("Do nothing if monoco is already installed", async () => {
    // monoco --version calls back with null error (success)
    execStub.withArgs("monoco --version").yields(null);

    await bootstrap.checkAndBootstrap();

    assert.strictEqual(showInfoStub.called, false);
    assert.strictEqual(showWarnStub.called, false);
  });

  test("Prompt install if monoco missing but uv present", async () => {
    // monoco missing
    execStub.withArgs("monoco --version").yields(new Error("not found"));
    // uv present
    execStub.withArgs("uv --version").yields(null);

    // User accepts
    showInfoStub.resolves("Install");

    await bootstrap.checkAndBootstrap();

    assert.strictEqual(showInfoStub.called, true);
    assert.strictEqual(createTerminalStub.called, true);
    assert.strictEqual(terminalShowSpy.called, true);
    // Expect toolkit install command
    assert.strictEqual(
      terminalSendTextSpy.calledWith("uv tool install monoco-toolkit"),
      true
    );
  });

  test("Prompt full install if monoco and uv missing", async () => {
    // monoco missing
    execStub.withArgs("monoco --version").yields(new Error("not found"));
    // uv missing
    execStub.withArgs("uv --version").yields(new Error("not found"));

    // User accepts
    showWarnStub.resolves("Install All");

    await bootstrap.checkAndBootstrap();

    assert.strictEqual(showWarnStub.called, true);
    assert.strictEqual(createTerminalStub.called, true);

    // Check commands based on platform logic (mocking os might be needed for strict platform test,
    // but let's assume linux/mac for default test environment or check what platform we are running)
    // Since we didn't mock process.platform, this test will run with actual platform strings.

    if (process.platform === "win32") {
      assert.strictEqual(
        terminalSendTextSpy.firstCall.args[0].includes(
          "irm https://astral.sh/uv/install.ps1"
        ),
        true
      );
    } else {
      assert.strictEqual(
        terminalSendTextSpy.firstCall.args[0].includes("curl -LsSf"),
        true
      );
    }
  });

  test("User cancel does nothing", async () => {
    execStub.withArgs("monoco --version").yields(new Error("not found"));
    execStub.withArgs("uv --version").yields(null);

    showInfoStub.resolves("Cancel");

    await bootstrap.checkAndBootstrap();

    assert.strictEqual(createTerminalStub.called, false);
  });
});
