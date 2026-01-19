"""
CLI Adapters for Agent Frameworks.
"""

import shutil
from typing import List
from pathlib import Path
from .protocol import AgentClient


class BaseCLIClient:
    def __init__(self, executable: str):
        self._executable = executable

    @property
    def name(self) -> str:
        return self._executable

    async def available(self) -> bool:
        return shutil.which(self._executable) is not None

    def _build_prompt(self, prompt: str, context_files: List[Path]) -> str:
        """Concatenate prompt and context files."""
        # Inject Language Rule
        try:
            from monoco.core.config import get_config

            settings = get_config()
            lang = settings.i18n.source_lang
            if lang:
                prompt = f"{prompt}\n\n[SYSTEM: LANGUAGE CONSTRAINT]\nThe project source language is '{lang}'. You MUST use '{lang}' for all thinking and reporting unless explicitly instructed otherwise."
        except Exception:
            pass

        full_prompt = [prompt]
        if context_files:
            full_prompt.append("\n\n--- CONTEXT FILES ---")
            for file_path in context_files:
                try:
                    full_prompt.append(f"\nFile: {file_path}")
                    full_prompt.append("```")
                    # Read file content safely
                    full_prompt.append(
                        file_path.read_text(encoding="utf-8", errors="replace")
                    )
                    full_prompt.append("```")
                except Exception as e:
                    full_prompt.append(f"Error reading {file_path}: {e}")
            full_prompt.append("--- END CONTEXT ---\n")
        return "\n".join(full_prompt)

    async def _run_command(self, args: List[str]) -> str:
        """Run the CLI command and return stdout."""
        # Using synchronous subprocess in async function for now
        # Ideally this should use asyncio.create_subprocess_exec
        import asyncio

        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            raise RuntimeError(
                f"Agent CLI failed (code {proc.returncode}): {error_msg}"
            )

        return stdout.decode().strip()


class GeminiClient(BaseCLIClient, AgentClient):
    """Adapter for Google Gemini CLI."""

    def __init__(self):
        super().__init__("gemini")

    async def execute(self, prompt: str, context_files: List[Path] = []) -> str:
        full_prompt = self._build_prompt(prompt, context_files)
        # Usage: gemini "prompt"
        return await self._run_command([self._executable, full_prompt])


class ClaudeClient(BaseCLIClient, AgentClient):
    """Adapter for Anthropic Claude CLI."""

    def __init__(self):
        super().__init__("claude")

    async def execute(self, prompt: str, context_files: List[Path] = []) -> str:
        full_prompt = self._build_prompt(prompt, context_files)
        # Usage: claude -p "prompt"
        return await self._run_command([self._executable, "-p", full_prompt])


class QwenClient(BaseCLIClient, AgentClient):
    """Adapter for Alibaba Qwen CLI."""

    def __init__(self):
        super().__init__("qwen")

    async def execute(self, prompt: str, context_files: List[Path] = []) -> str:
        full_prompt = self._build_prompt(prompt, context_files)
        # Usage: qwen "prompt"
        return await self._run_command([self._executable, full_prompt])


class KimiClient(BaseCLIClient, AgentClient):
    """Adapter for Moonshot Kimi CLI."""

    def __init__(self):
        super().__init__("kimi")

    async def execute(self, prompt: str, context_files: List[Path] = []) -> str:
        full_prompt = self._build_prompt(prompt, context_files)
        # Usage: kimi "prompt"
        return await self._run_command([self._executable, full_prompt])


_ADAPTERS = {
    "gemini": GeminiClient,
    "claude": ClaudeClient,
    "qwen": QwenClient,
    "kimi": KimiClient,
}


def get_agent_client(name: str) -> AgentClient:
    """Factory to get agent client by name."""
    if name not in _ADAPTERS:
        raise ValueError(f"Unknown agent provider: {name}")
    return _ADAPTERS[name]()
