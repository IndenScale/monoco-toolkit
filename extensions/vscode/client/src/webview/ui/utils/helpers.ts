/**
 * SVG icon constants
 */
export const ICONS = {
  // VS Code Codicons (Standard)
  // Unicode Symbols (Semantic)
  EPIC: "🚀", // Rocket - Big initiative
  FEATURE: "✨", // Sparkles - New value
  BUG: "🐞", // Lady beetle - Bug
  CHORE: "🔧", // Wrench - Maintenance
  ARCH: "🏛", // Building - Architecture
  FIX: "🩹", // Bandage - Quick fix

  // UI Icons (SVGs for Native Look)
  CHEVRON: `<svg class="icon" viewBox="0 0 16 16"><path d="M6 3l5 5-5 5-1-1 4-4-4-4 1-1z" fill="currentColor"/></svg>`,
  WEB: `<svg class="icon" viewBox="0 0 16 16"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 13a6 6 0 1 1 0-12 6 6 0 0 1 0 12zM8 3a5 5 0 0 0-4.57 3h9.14A5 5 0 0 0 8 3zM3.06 7a5.1 5.1 0 0 0 .37 4h9.14a5.12 5.12 0 0 0 .37-4H3.06zM8 13a5 5 0 0 0 4.57-3H3.43A5 5 0 0 0 8 13z" fill="currentColor"/></svg>`,
  SETTINGS: `<svg class="icon" viewBox="0 0 16 16"><path d="M9.1 4.4L8.6 2H7.4l-.5 2.4-.7.3-2-1.3-.9.8 1.3 2-.2.7-2.4.5v1.2l2.4.5.3.8-1.3 2 .8.8 2-1.3.8.3.4 2.3h1.2l.5-2.4.8-.3 2 1.3.8-.8-1.3-2 .3-.8 2.3-.4V7.4l-2.4-.5-.3-.8 1.3-2-.8-.8-2 1.3-.7-.2zM6.4 8a1.6 1.6 0 1 1 3.2 0 1.6 1.6 0 0 1-3.2 0z" fill="currentColor"/></svg>`,
  PLUS: `<svg class="icon" viewBox="0 0 16 16"><path d="M14 7v1H9v5H8V8H3V7h5V2h1v5h5z" fill="currentColor"/></svg>`,
  BACK: `<svg class="icon" viewBox="0 0 16 16"><path d="M7.7 3.3l-5 5H15v1H2.7l5 5-.7.7-5.45-5.46L1.1 9.1l.45-.46L7 2.6l.7.7z" fill="currentColor"/></svg>`,
  EXECUTION: `<svg class="icon" viewBox="0 0 16 16"><path d="M3 2l10 6-10 6V2z" fill="currentColor"/></svg>`,
  MORE: `<svg class="icon" viewBox="0 0 16 16"><path d="M8 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM8 4a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM8 14a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z" fill="currentColor"/></svg>`,
  FILTER: `<svg class="icon" viewBox="0 0 16 16"><path d="M6 12v-2h4v2H6zm-3-4v-2h10v2H3zm-2-4V2h14v2H1z" fill="currentColor"/></svg>`,
} as const;

/**
 * Get SVG icon for a given issue type
 */
export function getIcon(type: string): string {
  const t = (type || "").toUpperCase();
  if (t === "EPIC") {
    return ICONS.EPIC;
  }
  if (t === "ARCH") {
    return ICONS.ARCH;
  }
  if (t === "FEATURE") {
    return ICONS.FEATURE;
  }
  if (t === "BUG") {
    return ICONS.BUG;
  }
  if (t === "CHORE") {
    return ICONS.CHORE;
  }
  if (t === "FIX") {
    return ICONS.BUG;
  }
  return ICONS.FEATURE;
}

/**
 * Escape HTML special characters
 */
export function escapeHtml(unsafe: string | undefined): string {
  if (!unsafe) {
    return "";
  }
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Calculate status weight for sorting
 */
export function statusWeight(status: string): number {
  const map: Record<string, number> = {
    doing: 0,
    draft: 1,
    review: 2,
    backlog: 3,
    done: 4,
    closed: 5,
  };
  return map[status] ?? 99;
}

/**
 * Get status class for styling
 */
export function getStatusClass(issue: any): string {
  const s = (issue.stage || issue.status || "draft").toLowerCase();

  if (s.includes("doing") || s.includes("progress")) {
    return "doing";
  } else if (s.includes("review")) {
    return "review";
  } else if (s.includes("done")) {
    return "done";
  } else if (s.includes("closed")) {
    return "closed";
  } else {
    return "draft";
  }
}
