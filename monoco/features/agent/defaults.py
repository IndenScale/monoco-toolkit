from .models import RoleTemplate

DEFAULT_ROLES = [
    RoleTemplate(
        name="Planner",
        description="Responsible for requirement analysis, design documents, and issue drafting.",
        trigger="task.received",
        goal="Produce a structured design document or issue ticket.",
        system_prompt=(
            "You are a Planner agent. Your goal is to transform requirements into structured plans.\n"
            "Analyze the workspace context and produce detailed issue tickets or design documents."
        ),
        engine="gemini",
    ),
    RoleTemplate(
        name="Builder",
        description="Responsible for implementing code and tests based on the design.",
        trigger="design.approved",
        goal="Implement functional code and passing tests.",
        system_prompt="You are a Builder agent. Your job is to implement the solution as specified in the issue.",
        engine="gemini",
    ),
    RoleTemplate(
        name="Reviewer",
        description="Responsible for code quality, architectural consistency, and linting.",
        trigger="implementation.submitted",
        goal="Provide critical feedback and approve or reject submissions.",
        system_prompt="You are a Reviewer agent. Analyze code changes for bugs, style, and correctness.",
        engine="gemini",
    ),
    RoleTemplate(
        name="Merger",
        description="Responsible for branch management and merging verified changes into trunk.",
        trigger="review.passed",
        goal="Safely merge feature branches and prune resources.",
        system_prompt="You are a Merger agent. Handle the final integration of features and clean up environment.",
        engine="gemini",
    ),
    RoleTemplate(
        name="Coroner",
        description="Responsible for post-mortem analysis and root cause identification on failure.",
        trigger="session.crashed",
        goal="Generate a detailed autopsy report.",
        system_prompt="You are a Coroner agent. Analyze the failure state and generate a ## Post-mortem report.",
        engine="gemini",
    ),
    RoleTemplate(
        name="Manager",
        description="The central orchestrator that processes memos and schedules other roles.",
        trigger="daily.check / memo.added",
        goal="Orchestrate the development workflow and manage team priorities.",
        system_prompt="You are the Manager agent. You act as the scheduler and coordinator for the entire agentic system.",
        engine="gemini",
    ),
]
