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

        print(f"💀 [Apoptosis] Starting lifecycle for Session {session_id}")

        # 1. Kill
        self._kill(session)

        # 2. Autopsy
        try:
            self._perform_autopsy(session)
        except Exception as e:
            print(f"⚠️ Autopsy failed: {e}")

        # 3. Reset
        self._reset_environment(session)

        print(
            f"✅ [Apoptosis] Task {session.model.issue_id} has been reset and analyzed."
        )

    def _kill(self, session: RuntimeSession):
        print(f"🔪 Killing worker process for {session.model.id}...")
        session.terminate()
        session.model.status = "crashed"

    def _perform_autopsy(self, victim_session: RuntimeSession):
        print(
            f"🔍 Performing autopsy on {victim_session.model.id} via Coroner agent..."
        )

        # Start a Coroner session
        coroner_session = self.session_manager.create_session(
            victim_session.model.issue_id, self.coroner_role
        )

        # Context for the coroner
        context = {
            "description": f"The previous agent session ({victim_session.model.id}) for role '{victim_session.model.role_name}' crashed. Please analyze the environment and the Issue {victim_session.model.issue_id}, then write a ## Post-mortem section in the issue file."
        }

        coroner_session.start(context=context)
        print("📄 Coroner agent finished analysis.")

    def _reset_environment(self, session: RuntimeSession):
        print("🧹 Resetting environment (simulated git reset --hard)...")
        # In real impl:
        # import subprocess
        # subprocess.run(["git", "reset", "--hard"], check=True)
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
