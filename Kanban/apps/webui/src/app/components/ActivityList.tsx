import React from "react";
import { Card, Elevation, Icon, Intent, Spinner } from "@blueprintjs/core";
import { useDashboardStore, ActivityType } from "@monoco/kanban-core";

// Helper to format date
const formatDate = (dateStr: string) => {
    try {
        const date = new Date(dateStr);
        // Display relative time if possible, or just short date
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.round(diffMs / 60000);
        const diffHours = Math.round(diffMs / 3600000);
        const diffDays = Math.round(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    } catch (e) {
        return dateStr;
    }
};

const getActivityIcon = (type: ActivityType) => {
    switch (type) {
        case "created": return "add";
        case "closed": return "tick-circle";
        case "updated": return "edit";
        default: return "circle";
    }
};

const getActivityIntent = (type: ActivityType) => {
    switch (type) {
        case "created": return Intent.PRIMARY;
        case "closed": return Intent.SUCCESS;
        case "updated": return Intent.WARNING;
        default: return Intent.NONE;
    }
};

export default function ActivityList({ showHeader = true }: { showHeader?: boolean }) {
    const { stats, isLoading } = useDashboardStore();

    if (isLoading && !stats) {
        return (
            <div className="flex justify-center p-4">
                <Spinner size={24} intent={Intent.PRIMARY} />
            </div>
        );
    }

    if (!stats) return null;

    const { recent_activities } = stats;

    return (
        <Card elevation={Elevation.ONE} className="h-full flex flex-col">
            {showHeader && (
                <h3 className="text-lg font-semibold mb-4 text-text-primary border-b border-gray-100 pb-2">
                    Activity Feed
                </h3>
            )}
            
            <div className="flex-1 overflow-y-auto max-h-[400px] pr-2">
                {!recent_activities || recent_activities.length === 0 ? (
                    <div className="text-text-muted text-center py-8">
                        No recent activities found.
                    </div>
                ) : (
                    <div className="space-y-4">
                        {recent_activities.map((activity) => (
                            <div key={activity.id} className="flex items-start gap-3">
                                <div className="mt-1">
                                    <Icon 
                                        icon={getActivityIcon(activity.type)} 
                                        intent={getActivityIntent(activity.type)} 
                                        size={14}
                                    />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-baseline">
                                        <p className="font-medium text-text-primary text-sm truncate pr-2" title={activity.issue_title}>
                                            {activity.issue_title}
                                        </p>
                                        <span className="text-xs text-text-muted whitespace-nowrap flex-shrink-0">
                                            {formatDate(activity.timestamp)}
                                        </span>
                                    </div>
                                    <p className="text-xs text-text-muted mt-0.5 flex items-center gap-1">
                                        <span className="capitalize font-semibold">{activity.type}</span>
                                        <span>•</span>
                                        <span className="font-mono text-[10px] bg-gray-100 px-1 rounded">{activity.issue_id}</span>
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </Card>
    );
}
