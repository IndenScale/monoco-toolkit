"use client";

import React from "react";
import StatsBoard from "../components/StatsBoard";
import { useDaemonStore } from "@monoco-io/kanban-core";
import { Callout, NonIdealState, Button, Intent } from "@blueprintjs/core";
import Link from "next/link";

export default function DashboardPage() {
    const { status, projects } = useDaemonStore();

    if (status !== "connected") {
        return (
             <div className="p-8">
                <Callout intent="warning" title="Not Connected">
                    Please ensure the Monoco Daemon is running and connected.
                </Callout>
             </div>
        );
    }

    if (projects.length === 0) {
        return (
            <div className="flex-1 flex items-center justify-center p-6 h-full">
                <NonIdealState
                    icon="folder-open"
                    title="No Projects Found"
                    description="Get started by creating a new Monoco project or opening an existing one."
                    action={
                        <Link href="/issues">
                             <Button intent={Intent.PRIMARY} text="Go to Detailed" />
                        </Link>
                    }
                />
            </div>
        );
    }

    return (
        <main className="h-full flex flex-col font-sans overflow-hidden bg-canvas">
            <header className="px-6 py-6 shrink-0 z-10 border-b border-border-subtle bg-surface/50 backdrop-blur-sm">
                <h1 className="text-2xl font-bold text-text-primary tracking-tight mb-1">
                    Dashboard
                </h1>
                <p className="text-sm text-text-muted">
                    Global view of your project health and metrics.
                </p>
            </header>

            <div className="flex-1 overflow-y-auto p-6">
                 <StatsBoard />
            </div>
        </main>
    );
}
