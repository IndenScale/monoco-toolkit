from .manager import SessionManager
from .models import RoleTemplate

class ApoptosisManager:
    """
    Manages the controlled shutdown (Apoptosis) and investigation (Autopsy) 
    of failed agent sessions.
    """
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        
    def trigger_apoptosis(self, session_id: str) -> None:
        """
        Trigger the apoptosis process for a given session.
        1. Mark session as crashed.
        2. Spin up a Coroner agent to diagnose.
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return
            
        # 1. Mark as crashed
        session.model.status = "crashed"
        
        # 2. Start Coroner
        self._perform_autopsy(session)
        
    def _perform_autopsy(self, victim_session):
        coroner_role = RoleTemplate(
            name="Coroner",
            description="Investigates cause of death for failed agents.",
            trigger="system.crash",
            goal="Determine why the previous agent failed.",
            system_prompt="You are the Coroner. Analyze the logs.",
            engine="gemini"
        )
        
        coroner_session = self.session_manager.create_session(
            issue_id=victim_session.model.issue_id,
            role=coroner_role
        )
        
        coroner_session.start()
