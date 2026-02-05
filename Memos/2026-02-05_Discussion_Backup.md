# Discussion Backup: Monoco Agentic System & Daemon Evolution
**Date:** 2026-02-05
**Participants:** IndenScale (User), Monoco Agent (Kernel Worker)

## 1. Context & Problem Statement
- **Theoretical Base:** Adhering to "Principles of Agentic System" (DoD, Milestone, Invariance, Ralph Loop).
- **Core Pain Point:** Current `monoco-daemon` is a reactive trigger lacking state and global vision.
- **Critical Insight:** Human Code Review in Gitea/GitHub is often ceremonial. Domain experts cannot verify systems in IDEs. Testing coverage is naturally low.

## 2. Strategic Shift: "Evidence-First" L3
Instead of jumping directly to autonomous L4 (Self-evolving rules), we focus on making L3 **truly verifiable** for humans (HOTL).

### Key Proposal: Artifacts as Evidence
- **DoD Extension:** Moving from "Code-only" DoD to "Physical Evidence" DoD.
- **Evidence Types:** Screenshots (Web), stdout logs (CLI), temporary preview URLs.
- **Daemon's New Role:** Not just running agents, but acting as a "Proof Collector". It should automatically provision environments, capture evidence, and post it back to the Issue.

## 3. Implementation Roadmap (Draft)
1. **Artifacts Protocol:** Define how agents/daemon produce and link "Evidence" to Issues.
2. **Stateful Daemon (Daemon 2.0):** Implement session persistence to track attempts and failures (infrastructure for Ralph Loop).
3. **Preview Mechanism:** `monoco preview` command to generate visual/functional proof for non-technical stakeholders.

## 4. Pending Actions
- [ ] Define `Artifacts Protocol` schema.
- [ ] Investigate integration of preview environments (Docker/Local sandbox).
- [ ] Revisit `monoco/daemon/scheduler.py` to add state management.

---
*Note: This memo serves as a recovery point due to imminent IDE instability.*
