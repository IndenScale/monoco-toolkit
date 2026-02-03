"""
RunPytestAction - Action for running pytest tests.

Part of Layer 3 (Action Executor) in the event automation framework.
Executes pytest and parses results.
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from monoco.core.scheduler import AgentEvent
from monoco.core.router import Action, ActionResult

logger = logging.getLogger(__name__)


class PytestResult:
    """Result of a pytest execution."""
    
    def __init__(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        summary: Optional[Dict[str, Any]] = None,
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.summary = summary or {}
    
    @property
    def passed(self) -> bool:
        return self.returncode == 0
    
    @property
    def failed_count(self) -> int:
        return self.summary.get("failed", 0)
    
    @property
    def passed_count(self) -> int:
        return self.summary.get("passed", 0)
    
    @property
    def total_count(self) -> int:
        return self.summary.get("total", 0)


class RunPytestAction(Action):
    """
    Action that runs pytest tests.
    
    This action executes pytest with configurable options and
    parses the results for downstream processing.
    
    Example:
        >>> action = RunPytestAction(
        ...     test_path="tests/",
        ...     markers=["unit"],
        ...     cov=True,
        ... )
        >>> result = await action(event)
    """
    
    def __init__(
        self,
        test_path: Optional[str] = None,
        markers: Optional[List[str]] = None,
        cov: bool = False,
        cov_report: Optional[str] = None,
        verbose: bool = True,
        timeout: int = 300,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config)
        self.test_path = test_path or "."
        self.markers = markers or []
        self.cov = cov
        self.cov_report = cov_report
        self.verbose = verbose
        self.timeout = timeout
        self._last_result: Optional[PytestResult] = None
    
    @property
    def name(self) -> str:
        return "RunPytestAction"
    
    async def can_execute(self, event: AgentEvent) -> bool:
        """Always can execute (no preconditions)."""
        return True
    
    async def execute(self, event: AgentEvent) -> ActionResult:
        """Run pytest tests."""
        logger.info(f"Running pytest for {self.test_path}")
        
        try:
            result = await self._run_pytest()
            self._last_result = result
            
            if result.passed:
                return ActionResult.success_result(
                    output={
                        "passed": result.passed_count,
                        "failed": result.failed_count,
                        "total": result.total_count,
                    },
                    metadata={
                        "stdout_preview": result.stdout[:500] if result.stdout else None,
                    },
                )
            else:
                return ActionResult.failure_result(
                    error=f"Tests failed: {result.failed_count} failures",
                    metadata={
                        "passed": result.passed_count,
                        "failed": result.failed_count,
                        "total": result.total_count,
                        "stderr_preview": result.stderr[:500] if result.stderr else None,
                    },
                )
        
        except Exception as e:
            logger.error(f"Pytest execution failed: {e}")
            return ActionResult.failure_result(error=str(e))
    
    async def _run_pytest(self) -> PytestResult:
        """Execute pytest subprocess."""
        cmd = ["python", "-m", "pytest"]
        
        # Add test path
        cmd.append(self.test_path)
        
        # Add markers
        if self.markers:
            marker_expr = " and ".join(self.markers)
            cmd.extend(["-m", marker_expr])
        
        # Add coverage
        if self.cov:
            cmd.append("--cov")
            if self.cov_report:
                cmd.extend(["--cov-report", self.cov_report])
        
        # Add verbosity
        if self.verbose:
            cmd.append("-v")
        
        # Add JSON report for parsing
        cmd.extend(["--tb=short", "-q"])
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        # Run subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"Pytest timed out after {self.timeout}s")
        
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")
        
        # Parse summary
        summary = self._parse_summary(stdout_str)
        
        return PytestResult(
            returncode=process.returncode,
            stdout=stdout_str,
            stderr=stderr_str,
            summary=summary,
        )
    
    def _parse_summary(self, output: str) -> Dict[str, int]:
        """Parse pytest summary from output."""
        summary = {"passed": 0, "failed": 0, "error": 0, "skipped": 0, "total": 0}
        
        # Look for summary line like "5 passed, 2 failed in 0.5s"
        import re
        pattern = r"(\d+)\s+(passed|failed|error|skipped)"
        matches = re.findall(pattern, output)
        
        for count, status in matches:
            summary[status] = int(count)
            summary["total"] += int(count)
        
        return summary
    
    def get_last_result(self) -> Optional[PytestResult]:
        """Get the last pytest result."""
        return self._last_result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get action statistics."""
        stats = super().get_stats()
        stats.update({
            "test_path": self.test_path,
            "markers": self.markers,
            "last_result": {
                "passed": self._last_result.passed if self._last_result else None,
                "failed": self._last_result.failed_count if self._last_result else None,
            } if self._last_result else None,
        })
        return stats
