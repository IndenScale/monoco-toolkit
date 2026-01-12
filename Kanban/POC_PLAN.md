# Monoco Kanban POC Plan (Web-First)

Due to the absence of `cargo` (Rust) in the current environment, we will prioritize the **Web Shell** implementation while establishing the Monorepo architecture to support the Desktop Shell in the future.

## 1. Project Structure (Monorepo)

We will organize `Kanban/` as an npm workspace:

```text
Kanban/
├── package.json (Workspaces root)
├── packages/
│   └── core/       # Shared business logic, types, and state (Zustand)
├── apps/
│   ├── web/        # Next.js App (The current POC target)
│   └── desktop/    # Tauri App (Placeholder for future)
└── docs/
```

## 2. Technology Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui (if feasible, otherwise plain Tailwind)
- **State**: Zustand (in `packages/core`)
- **Data Mock**: Since we cannot access the local FS directly from the browser easily without a backend bridge, we will create a `FileSystemAdapter` interface with a `MockFileSystem` implementation for the POC.

## 3. Implementation Steps

1.  **Scaffold**: Initialize the directory structure and root `package.json`.
2.  **Core**: Create `packages/core` with basic `Issue` and `Task` type definitions and a `TaskStore`.
3.  **Web App**: Initialize `apps/web` using `create-next-app`.
4.  **Integration**: Link `core` to `web` and display a list of "Tasks" fetched from the mock adapter.
5.  **UI**: Implement a simplified "Linear-like" list view.

## 4. Verification

- Build the `core` package.
- Run the `web` app in development mode.
- Verify that tasks (mocks) are rendered correctly.
