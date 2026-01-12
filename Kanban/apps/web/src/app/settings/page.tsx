"use client";

import React from "react";
import { Card, Elevation, Switch, Button, FormGroup, InputGroup, Intent } from "@blueprintjs/core";

export default function SettingsPage() {
    return (
        <main className="h-full flex flex-col font-sans overflow-hidden bg-canvas">
            <header className="px-6 py-6 shrink-0 z-10 border-b border-border-subtle bg-surface/50 backdrop-blur-sm">
                <h1 className="text-2xl font-bold text-text-primary tracking-tight mb-1">
                    Settings
                </h1>
                <p className="text-sm text-text-muted">
                    Manage your preferences and project configurations.
                </p>
            </header>

            <div className="flex-1 overflow-auto px-6 py-6">
                <div className="max-w-3xl space-y-6">
                    <Card elevation={Elevation.ONE}>
                        <h3 className="text-lg font-semibold mb-4 text-text-primary">Appearance</h3>
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h5 className="font-medium text-text-primary">Dark Mode</h5>
                                <p className="text-sm text-text-muted">Use dark theme for the interface.</p>
                            </div>
                            <Switch checked={true} readOnly />
                        </div>
                        <div className="flex items-center justify-between">
                            <div>
                                <h5 className="font-medium text-text-primary">Compact View</h5>
                                <p className="text-sm text-text-muted">Show more content on the screen.</p>
                            </div>
                            <Switch />
                        </div>
                    </Card>

                    <Card elevation={Elevation.ONE}>
                        <h3 className="text-lg font-semibold mb-4 text-text-primary">Connection</h3>
                        <FormGroup label="Daemon URL" labelInfo="(required)">
                            <InputGroup defaultValue="http://127.0.0.1:8642" />
                        </FormGroup>
                        <Button intent={Intent.PRIMARY} text="Test Connection" />
                    </Card>
                    
                    <Card elevation={Elevation.ONE}>
                        <h3 className="text-lg font-semibold mb-4 text-text-primary">About</h3>
                        <p className="text-text-muted mb-2">Monoco Premium Cockpit v0.1.0</p>
                        <p className="text-text-muted text-sm">
                            Running on local daemon.
                        </p>
                    </Card>
                </div>
            </div>
        </main>
    );
}
