from .models import Transition
from .machine import StateMachine
from .config import DEFAULT_ISSUE_CONFIG
from monoco.core.config import get_config

def get_engine(project_root: Optional[str] = None) -> StateMachine:
    # 1. Load Core Config (merges workspace & project yamls)
    core_config = get_config(project_root)
    
    # 2. Start with Defaults
    # Use model_copy to avoid mutating the global default instance
    final_config = DEFAULT_ISSUE_CONFIG.model_copy(deep=True)
    
    # 3. Merge User Overrides
    if core_config.issue:
        # core_config.issue is already an IssueSchemaConfig (parse/validated by Pydantic)
        # We just need to merge it.
        final_config.merge(core_config.issue)

    return StateMachine(final_config)
