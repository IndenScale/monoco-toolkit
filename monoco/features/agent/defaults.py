from .models import RoleTemplate

DEFAULT_ROLES = [
    RoleTemplate(
        name="Default",
        description="A generic, jack-of-all-trades agent used when no specific role is configured.",
        trigger="task.dispatch",
        goal="Complete the assigned task.",
        system_prompt="You are a helpful Agent. Complete the task assigned to you.",
        engine="gemini",
    )
]
