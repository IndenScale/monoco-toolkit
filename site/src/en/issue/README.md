# Monoco Issue System

**Monoco Issue System** is the core task orchestration layer for Agentic Engineering.

Unlike traditional tools like Jira or Linear, it is not designed to isolate humans and machines, but for **Human-Agent Collaboration**. it provides a set of deterministic, verifiable protocols that allow AI Agents to safely participate in the software engineering lifecycle.

---

## 📚 Core Documentation

Please read the following documents in order to establish a complete understanding:

### [Concepts: Why Issues?](./concepts.md)

> Explore the problem of entropy in software engineering and the challenges Agents face in collaboration (hallucinations, amnesia, divergence). Explain how Monoco solves these problems through "Issue as Code".

### [Structural Anatomy](./configuration.md) (Actually Configuration/Structure)

> Details the static structure of an Issue. Including YAML Front Matter as a machine interface (with file tracking) and Markdown Body as a human interface. Introduces static verification mechanisms.

### [User Manual: Workflow Tools](./manual.md)

> CLI command reference manual. Covers the entire process from creation, starting branches, syncing context (`sync-files`) to submission for acceptance.

### [Query Syntax](./query_syntax.md)

> Query and filter Issues using SQL-like logic.

---

## 📖 Strategy & Governance

- **Strict Git Workflow**: Monoco enforces a branch-per-issue strategy to ensure isolation.
- **Agent Protocol**: How Monoco shapes Agent behavior through Skill injection and environment constraints (Linter).
