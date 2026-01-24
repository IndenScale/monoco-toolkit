from .models import RoleTemplate

DEFAULT_ROLES = [
    RoleTemplate(
        name="crafter",
        description="Responsible for initial design and research.",
        trigger="issue.created",
        goal="Output design document",
        tools=["read_file", "search_web", "view_file_outline"],
        system_prompt="You are a Crafter agent. Your job is to analyze the request and create a design document.",
    ),
    RoleTemplate(
        name="builder",
        description="Responsible for implementation.",
        trigger="design.approved",
        goal="Implement code and tests",
        tools=["read_file", "write_to_file", "run_command", "git"],
        system_prompt="You are a Builder agent. Your job is to implement the code based on the design.",
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
    ),
]
