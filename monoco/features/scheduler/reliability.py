from .manager import SessionManager
from .session import RuntimeSession
from .defaults import DEFAULT_ROLES


class ApoptosisManager:
    """
    Handles the 'Apoptosis' (Programmed Cell Death) lifecycle for agents.
    Ensures that failing agents are killed, analyzed, and the environment is reset.
    """

    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        # Find coroner role
        self.coroner_role = next(
            (r for r in DEFAULT_ROLES if r.name == "coroner"), None
        )
        if not self.coroner_role:
            raise ValueError("Coroner role not defined!")

    def check_health(self, session: RuntimeSession) -> bool:
        """
        Check if a session is healthy.
        In a real implementation, this would check heartbeat, CPU usage, or token limits.
        """
        # Placeholder logic: Random failure or external flag?
        # For now, always healthy unless explicitly marked 'crashed' (which we can simulate)
        if hasattr(session, "simulate_crash") and session.simulate_crash:
            return False
        return True

    def trigger_apoptosis(self, session_id: str):
        """
        Execute the full death and rebirth cycle.
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            print(f"Session {session_id} not found for apoptosis.")
            return

        print(f"💀 Apoptosis triggered for Session {session_id}")

        # 1. Kill
        self._kill(session)

        # 2. Autopsy
        self._perform_autopsy(session)

        # 3. Reset
        self._reset_environment(session)

        # 4. Retry (Reincarnation)
        # TODO: Implement retry logic with max_retries check
        # self._retry(session)

    def _kill(self, session: RuntimeSession):
        print(f"🔪 Killing worker process for {session.model.id}...")
        session.terminate()
        # Ensure status is crashed/dead, not just terminated nicely
        session.model.status = "crashed"

    def _perform_autopsy(self, victim_session: RuntimeSession):
        print(f"🔍 Performing autopsy on {victim_session.model.id}...")
        # Start a Coroner session
        # Ideally, this runs in the SAME context (directory) but is a different agent
        coroner_session = self.session_manager.create_session(
            victim_session.model.issue_id, self.coroner_role
        )
        coroner_session.start()

        # Simulate autopsy work
        import time

        time.sleep(0.5)
        print("📄 Coroner wrote 'post_mortem.md'.")

        coroner_session.terminate()

    def _reset_environment(self, session: RuntimeSession):
        print("🧹 Resetting environment (git reset --hard)...")
        # In real impl: subprocess.run(["git", "reset", "--hard"], cwd=project_root)
        pass

    def _retry(self, session: RuntimeSession):
        print("🔄 Reincarnating session...")
        # Create a new session with the same role and issue
        new_session = self.session_manager.create_session(
            session.model.issue_id,
            # We need to find the original role object.
            # Simplified: assuming we can find it by name or pass it.
            # For now, just placeholder.
            session.worker.role,
        )
        new_session.start()
