"use client";

import React from "react";
import { NonIdealState, Button, Intent } from "@blueprintjs/core";

export default function ComponentsPage() {
    return (
        <main className="h-full flex flex-col font-sans overflow-hidden bg-canvas">
            <header className="px-6 py-6 shrink-0 z-10 border-b border-border-subtle bg-surface/50 backdrop-blur-sm">
                <h1 className="text-2xl font-bold text-text-primary tracking-tight mb-1">
                    Components
                </h1>
                <p className="text-sm text-text-muted">
                    Architecture and component dependency analysis.
                </p>
            </header>

            <div className="flex-1 flex items-center justify-center p-6">
                <NonIdealState
                    icon="cube"
                    title="Component Analysis"
                    description="This feature requires the Monoco Analysis Service which is currently under development. Check back later for architectural insights."
                    action={
                        <Button intent={Intent.PRIMARY} text="View Roadmap" onClick={() => window.open('https://github.com/monoco/roadmap', '_blank')} />
                    }
                />
            </div>
        </main>
    );
}
