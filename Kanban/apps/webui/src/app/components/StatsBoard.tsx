import React from "react";
import { Card, Elevation, Icon, Intent, Spinner, Tag } from "@blueprintjs/core";
import { useDashboardStore } from "@monoco-io/kanban-core";

export default function StatsBoard() {
  const { stats, isLoading } = useDashboardStore();

  if (isLoading && !stats) {
     return (
        <div className="flex justify-center p-4">
            <Spinner size={24} intent={Intent.PRIMARY} />
        </div>
     );
  }

  if (!stats) return null;

  const { total_backlog, completed_this_week, blocked_issues_count, velocity_trend } = stats;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      {/* Backlog */}
      <Card elevation={Elevation.ONE} className="flex flex-col justify-between">
        <div className="flex justify-between items-start mb-2">
          <h5 className="text-text-muted text-sm font-semibold uppercase tracking-wider">
            Total Backlog
          </h5>
          <Icon icon="inbox" className="text-text-muted" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-text-primary">{total_backlog}</span>
          <span className="text-xs text-text-muted">items</span>
        </div>
      </Card>

      {/* Completed This Week */}
      <Card elevation={Elevation.ONE} className="flex flex-col justify-between">
        <div className="flex justify-between items-start mb-2">
          <h5 className="text-text-muted text-sm font-semibold uppercase tracking-wider">
            Completed (Week)
          </h5>
          <Icon icon="tick-circle" className="text-emerald-500" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-text-primary">
            {completed_this_week}
          </span>
          <span className="text-xs text-emerald-500">issues</span>
        </div>
      </Card>

      {/* Blocked Issues */}
      <Card elevation={Elevation.ONE} className="flex flex-col justify-between">
        <div className="flex justify-between items-start mb-2">
          <h5 className="text-text-muted text-sm font-semibold uppercase tracking-wider">
            Blocked
          </h5>
          <Icon icon="ban-circle" className="text-red-500" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-text-primary">
            {blocked_issues_count}
          </span>
          <span className="text-xs text-red-500">issues</span>
        </div>
        {blocked_issues_count > 0 && (
            <div className="mt-2">
                <Tag minimal intent={Intent.DANGER}>Attention Needed</Tag>
            </div>
        )}
      </Card>

      {/* Velocity Trend */}
      <Card elevation={Elevation.ONE} className="flex flex-col justify-between">
        <div className="flex justify-between items-start mb-2">
          <h5 className="text-text-muted text-sm font-semibold uppercase tracking-wider">
            Velocity Trend
          </h5>
          <Icon icon="chart" className="text-blue-500" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-text-primary">
            {velocity_trend > 0 ? "+" : ""}{velocity_trend}
          </span>
          <span className="text-xs text-text-muted">vs last week</span>
        </div>
        <div className="mt-2">
             <Icon 
                icon={velocity_trend >= 0 ? "trending-up" : "trending-down"} 
                intent={velocity_trend >= 0 ? Intent.SUCCESS : Intent.WARNING}
                className="mr-1"
             />
             <span className={`text-xs ${velocity_trend >= 0 ? "text-emerald-500" : "text-amber-500"}`}>
                 {velocity_trend >= 0 ? "Increasing" : "Decreasing"}
             </span>
        </div>
      </Card>
    </div>
  );
}
