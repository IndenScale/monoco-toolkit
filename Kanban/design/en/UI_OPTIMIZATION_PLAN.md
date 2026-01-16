# Monoco Kanban UI Optimization Plan

## 1. Design Aesthetic: "Monoco Prism"

To achieve a professional, premium, and "wowed" user experience, we will adopt the "Monoco Prism" design language.

### Core Principles

- **Depth & Glass**: Heavy use of glassmorphism (backdrop-blur) and layered z-indexes to create depth.
- **Vibrant Gradients**: Use subtle but rich gradients for primary actions and accents, avoiding flat primary colors.
- **Data Density**: As a developer tool, prioritize information density but maintain breathability through whitespace and consistent grouping.
- **Motion**: Micro-interactions on hover, focus, and state changes.

### Color Palette (Tailwind Mappings)

- **Canvas**: `bg-slate-950` (Deep Space)
- **Surface**: `bg-slate-900/50` (Glassy Dark)
- **Borders**: `border-slate-800`
- **Primary Gradient**: `from-blue-500 to-indigo-600`
- **Accents**:
  - **Epic**: Purple/Pink Gradient
  - **Feature**: Blue/Cyan Gradient
  - **Chore**: Slate/Gray (Subtle)
  - **Fix**: Red/Orange (Alert)

### Typography

- **Headings**: Inter, tracking-tight, font-bold.
- **Monospace**: JetBrains Mono or Fira Code for IDs and code snippets.

## 2. Visualization: The "Issue Neural Net"

We will replace/augment the simple list view with a "Neural Net" visualization of the project state.

### Tech Stack

- **Library**: `reactflow` (Interactive node-based graph).
- **Layout**: `dagre` (Directed Acyclic Graph) for automatic hierarchical layout.

### Node Design

Each node (Issue) will be a custom React Component containing:

- **Header**: ID + Type Icon (Color coded).
- **Body**: Truncated Title.
- **Footer**: Status Badge + Progress (if applicable).
- **Handles**: Connection points for dependencies.

### Graph Logic

- **Hierarchy**:
  - Epics at Top (Rank 0).
  - Features (Rank 1).
  - Tasks (Chores/Fixes) (Rank 2).
- **Edges**:
  - **Parent-Child**: Solid line, thicker.
  - **Dependency**: Dashed line, animated if blocking.
  - **Related**: Dotted line, subtle gray.

## 3. Interaction & Navigation

### Dynamic Routing

- **Standard**: `/issues` (List/Graph Toggle).
- **Detail**: `/issues/[id]` (Full page) or `?preview=[id]` (Slide-over panel).
- **Link Jumping**: Clicking a dependency in any view opens the Slide-over panel for that issue without losing context.

### "Focus Mode"

- Clicking an issue in the graph dims all non-connected nodes, highlighting the "Critical Path" for that specific item.

---

## Implementation Roadmap

1.  **Phase 1: Foundation (Theming)**
    - Update `globals.css` with new variables.
    - Create `LayoutShell` component (Sidebar + Glass Header).
2.  **Phase 2: Data Transformation**
    - Implement `layout-utils.ts`: `(issues: Issue[]) => { nodes, edges }` using `dagre`.
3.  **Phase 3: Components**
    - `IssueNode`: Custom ReactFlow node.
    - `IssueGraph`: Main canvas wrapper.
4.  **Phase 4: Routing & Details**
    - Implement `IssueSlideOver` (using Blueprint Drawer or custom).
    - Connect "Related" links in `IssueList` to open SlideOver.
