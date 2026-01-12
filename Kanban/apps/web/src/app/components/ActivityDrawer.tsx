"use client";

import React from "react";
import { Drawer, Position, Classes, Icon, Intent, Spinner, Card, Elevation } from "@blueprintjs/core";
import { useDashboardStore, ActivityItem, ActivityType } from "@monoco/kanban-core";

interface ActivityDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

function getActivityIcon(type: ActivityType): any {
  switch (type) {
    case "created":
      return "add";
    case "updated":
      return "edit";
    case "closed":
      return "tick-circle";
    default:
      return "notifications";
  }
}

function getActivityIntent(type: ActivityType): Intent {
  switch (type) {
    case "created":
      return Intent.SUCCESS;
    case "updated":
      return Intent.PRIMARY;
    case "closed":
      return Intent.DANGER; // or SUCCESS, but closed often implies finished which can be good
    default:
      return Intent.NONE;
  }
}

function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString();
  } catch (e) {
    return timestamp;
  }
}

export default function ActivityDrawer({ isOpen, onClose }: ActivityDrawerProps) {
  const { stats, isLoading } = useDashboardStore();
  const activities = stats?.recent_activities || [];

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      position={Position.RIGHT}
      size="350px"
      title="Activity Feed"
      canOutsideClickClose={true}
      hasBackdrop={true}
    >
      <div className={Classes.DRAWER_BODY}>
        <div className="h-full p-4 overflow-y-auto">
            {isLoading && !stats ? (
                <div className="flex justify-center p-4">
                    <Spinner size={24} />
                </div>
            ) : activities.length === 0 ? (
                <div className="text-center text-gray-500 mt-4">
                    No recent activities
                </div>
            ) : (
                <div className="space-y-3">
                    {activities.map((activity) => (
                        <Card key={activity.id} elevation={Elevation.ZERO} className="!bg-opacity-50 !p-3 border border-gray-200 dark:border-gray-700">
                            <div className="flex items-start gap-3">
                                <div className={`mt-1 p-1 rounded-full bg-opacity-10`} >
                                     <Icon icon={getActivityIcon(activity.type)} intent={getActivityIntent(activity.type)} size={16} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium truncate" title={activity.issue_title}>
                                        {activity.issue_title}
                                    </div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                        {activity.description || activity.type}
                                    </div>
                                    <div className="text-[10px] text-gray-400 mt-2 text-right">
                                        {formatTime(activity.timestamp)}
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </div>
      </div>
    </Drawer>
  );
}
