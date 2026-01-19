# Monoco Issue System: The Foundation of AI-Native Collaboration

## 1. Why do we need Issues?

In software engineering, **Entropy** is the eternal enemy. As the codebase grows, system complexity rises exponentially.

The invention of **Issues** (tickets/tasks) is meant to combat this entropy. It is more than just a "to-do list"; it is:

- **Minimal Unit of Value**: Defines "Why and What" we are doing.
- **Responsibility Boundary**: Clarifies "When will it start, when will it end, and who is responsible."
- **Contract**: A consensus agreement between Product Managers, Architects, and Developers.

Without Issues, development is a chaotic pile; with Issues, development is built through a series of deterministic "atomic commits."

## 2. Why do Agents need Issues even more?

If human engineers need Issues for collaboration, **AI Agents** have a **fatal** requirement for them.

### The Three Achilles' Heels of Agents

1.  **Hallucination**: If the context is fuzzy, Agents will fill in the gaps with wrong assumptions.
2.  **Amnesia**: Agents have no long-term memory. Without persistent state records, they get lost after multiple rounds of dialogue.
3.  **Divergence**: Without strict tracks, Agent behavior can unpredictably drift from the original intent.

### Monoco's Solution: Issue as Code

Monoco re-invents the Issue system specifically to solve the challenges of human-machine collaboration. Toying with Issues as **"Anchors"**:

- **Structured Context**: Provides unambiguous input for Agents via Markdown Frontmatter and Body.
- **Persistent State Machine**: Solidifies Agent behavior states (Doing, Review, Done) in the file system.
- **Deterministic Validation**: Uses Linters to check task definitions like code, rejecting vague instructions.

In Monoco, **an Issue is your only credential for talking to an Agent**. Do not assign long-term tasks in a chat box; write them as Issues.

---

**Next Chapter**: [01. Structure: Universal Atom](./01_structure.md)
