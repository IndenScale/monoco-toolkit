from .models import RoleTemplate

DEFAULT_ROLES = [
    RoleTemplate(
        name="crafter",
        description="Responsible for initial design, research, and drafting issues from descriptions.",
        trigger="task.received",
        goal="Produce a structured Issue file and/or detailed design document.",
        tools=[
            "create_issue_file",
            "read_file",
            "search_web",
            "view_file_outline",
            "write_to_file",
        ],
        system_prompt=(
            "You are a Crafter agent. Your goal is to turn vague ideas into structured engineering plans.\n"
            "If the user provides a description, use 'monoco issue create' and 'monoco issue update' to build the task.\n"
            "If the user provides an existing Issue, analyze the context and provide a detailed design or implementation plan."
        ),
        engine="gemini",
    ),
    RoleTemplate(
        name="builder",
        description="Responsible for implementation.",
        trigger="design.approved",
        goal="Implement code and tests",
        tools=["read_file", "write_to_file", "run_command", "git"],
        system_prompt="You are a Builder agent. Your job is to implement the code based on the design.",
        engine="gemini",
    ),
    RoleTemplate(
        name="auditor",
        description="Responsible for code review.",
        trigger="implementation.submitted",
        goal="Review code and provide feedback",
        tools=[
            "read_file",
            "read_terminal",
            "run_command",
        ],  # Assumed read_diff and lint are via run_command
        system_prompt="You are an Auditor agent. Your job is to review the code for quality and correctness.",
        engine="gemini",
    ),
    RoleTemplate(
        name="coroner",
        description="Responsible for analyzing failure root causes (Autopsy).",
        trigger="session.crashed",
        goal="Produce a post-mortem report",
        tools=["read_file", "read_terminal", "git_log"],
        system_prompt="You are a Coroner agent. Your job is to analyze why the previous session failed and write a post-mortem report.",
        engine="gemini",
    ),
]
