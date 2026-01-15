import * as path from "path";
import * as fs from "fs";
import * as os from "os";

const DEFAULT_ACTIONS = [
  {
    name: "refine",
    filename: "refine.prompty",
    content: `---
name: refine
description: Refine and improve the current issue content at any stage.
authors: [Monoco]
model:
  api: chat
inputs:
  file:
    type: string
---
You are an expert Product Manager and Technical Writer.
Review and refine the following issue content to improve clarity, structure, and completeness.
Ensure proper formatting and that all sections are well-articulated.

# Context
{{file}}
`,
  },
  {
    name: "draft",
    filename: "draft.prompty",
    content: `---
name: draft
description: Generate a technical implementation plan and tasks.
authors: [Monoco]
model:
  api: chat
inputs:
  file:
    type: string
when:
  stageMatch: "draft"
---
You are a Senior Software Architect.
Review this feature and generate a detailed Technical Implementation Plan.
Break it down into actionable sub-tasks for the "Technical Tasks" section.

# Feature
{{file}}
`,
  },
  {
    name: "implement",
    filename: "implement.prompty",
    content: `---
name: implement
description: Generate implementation code or guide the development.
authors: [Monoco]
model:
  api: chat
inputs:
  file:
    type: string
when:
  stageMatch: "doing"
---
You are an expert Developer.
Based on the objective and technical tasks in this ticket, provide the implementation logic.
Focus on clean code and SOLID principles.

# Ticket
{{file}}
`,
  },
  {
    name: "audit",
    filename: "audit.prompty",
    content: `---
name: audit
description: Audit the implementation and delivery report for quality assurance.
authors: [Monoco]
model:
  api: chat
inputs:
  file:
    type: string
when:
  stageMatch: "review"
---
You are a Quality Assurance Engineer.
Perform a critical audit of the work described and the delivery report in this ticket.
Point out potential bugs, edge cases, and areas for improvement.
Verify that all acceptance criteria have been met.

# Submitted Work
{{file}}
`,
  },
];

export async function bootstrapActions() {
  const actionsDir = path.join(os.homedir(), ".monoco", "actions");

  try {
    if (!fs.existsSync(actionsDir)) {
      fs.mkdirSync(actionsDir, { recursive: true });
    }

    for (const action of DEFAULT_ACTIONS) {
      const filePath = path.join(actionsDir, action.filename);
      if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, action.content, "utf8");
        console.log(`[Monoco] Bootstrapped default action: ${action.name}`);
      }
    }
  } catch (error) {
    console.error("[Monoco] Failed to bootstrap actions:", error);
  }
}
