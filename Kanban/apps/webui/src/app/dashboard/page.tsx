"use client";

import MergedPageHeader from "../components/MergedPageHeader";
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
      <MergedPageHeader title="Dashboard" />

      <div className="flex-1 overflow-y-auto p-6">
        <StatsBoard />
      </div>
    </main>
  );
}
