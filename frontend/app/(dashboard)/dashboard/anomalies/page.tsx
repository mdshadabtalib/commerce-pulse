'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, TrendingDown, TrendingUp, CheckCircle, Clock } from 'lucide-react';

import { formatCurrency, formatTimeAgo } from '@/lib/utils';
import { KPICard } from '@/components/dashboard/kpi-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { AnomalyResponse, AnomalySeverity, AnomalyStatus } from '@/types';

const SEVERITY_CONFIG = {
  low: { color: 'info', icon: AlertTriangle },
  medium: { color: 'warning', icon: AlertTriangle },
  high: { color: 'destructive', icon: AlertTriangle },
  critical: { color: 'destructive', icon: AlertTriangle },
};

const STATUS_CONFIG = {
  open: { color: 'destructive', label: 'Open' },
  investigating: { color: 'warning', label: 'Investigating' },
  acknowledged: { color: 'info', label: 'Acknowledged' },
  resolved: { color: 'success', label: 'Resolved' },
};

export default function AnomaliesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['anomalies', 'list'],
    queryFn: async () => {
      return {
        kpis: {
          total_anomalies: 14,
          critical: 2,
          open: 6,
          resolved_today: 8,
        },
        anomalies: [
          {
            id: '1',
            anomaly_key: 'revenue-spike-2024-01-28',
            title: 'Unexpected revenue spike detected',
            description: 'Revenue increased by 245% compared to the same day last week',
            severity: 'high' as AnomalySeverity,
            status: 'investigating' as AnomalyStatus,
            direction: 'spike' as const,
            metric: 'revenue',
            metric_value: 85420,
            expected_value: 34800,
            deviation_percentage: 245.4,
            category: 'revenue',
            detected_at: '2024-01-28T14:30:00Z',
            window_start: '2024-01-28T00:00:00Z',
            window_end: '2024-01-28T23:59:59Z',
          },
          {
            id: '2',
            anomaly_key: 'conversion-drop-2024-01-27',
            title: 'Conversion rate dropped significantly',
            description: 'Conversion rate fell from 4.2% to 1.8% in the last 24 hours',
            severity: 'critical' as AnomalySeverity,
            status: 'open' as AnomalyStatus,
            direction: 'drop' as const,
            metric: 'conversion_rate',
            metric_value: 0.018,
            expected_value: 0.042,
            deviation_percentage: -57.1,
            category: 'conversion',
            detected_at: '2024-01-27T18:45:00Z',
            window_start: '2024-01-27T00:00:00Z',
            window_end: '2024-01-28T00:00:00Z',
          },
          {
            id: '3',
            anomaly_key: 'order-volume-spike-2024-01-26',
            title: 'Unusual order volume increase',
            description: 'Order volume 180% higher than expected during off-peak hours',
            severity: 'medium' as AnomalySeverity,
            status: 'resolved' as AnomalyStatus,
            direction: 'spike' as const,
            metric: 'orders',
            metric_value: 420,
            expected_value: 150,
            deviation_percentage: 180.0,
            category: 'orders',
            detected_at: '2024-01-26T03:15:00Z',
            window_start: '2024-01-26T00:00:00Z',
            window_end: '2024-01-26T06:00:00Z',
          },
        ] as AnomalyResponse[],
      };
    },
  });

  const kpis = data?.kpis;
  const anomalies = data?.anomalies || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Anomaly Detection</h1>
        <p className="text-muted-foreground mt-1">
          Monitor and investigate unusual patterns in your data
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <KPICard
          title="Total Anomalies"
          value={kpis?.total_anomalies || 0}
          icon={AlertTriangle}
          loading={isLoading}
        />
        <KPICard
          title="Critical"
          value={kpis?.critical || 0}
          icon={AlertTriangle}
          badge="High Priority"
          badgeVariant="destructive"
          loading={isLoading}
        />
        <KPICard
          title="Open"
          value={kpis?.open || 0}
          icon={Clock}
          loading={isLoading}
        />
        <KPICard
          title="Resolved Today"
          value={kpis?.resolved_today || 0}
          icon={CheckCircle}
          loading={isLoading}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-[400px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="space-y-4">
              {anomalies.map((anomaly) => {
                const DirectionIcon = anomaly.direction === 'spike' ? TrendingUp : TrendingDown;
                return (
                  <div
                    key={anomaly.id}
                    className="flex items-start gap-4 rounded-lg border border-border p-4 transition-all hover:shadow-md hover:border-primary/50"
                  >
                    <div className={`p-2 rounded-lg ${
                      anomaly.severity === 'critical' || anomaly.severity === 'high'
                        ? 'bg-destructive/10 text-destructive'
                        : anomaly.severity === 'medium'
                        ? 'bg-warning/10 text-warning'
                        : 'bg-info/10 text-info'
                    }`}>
                      <AlertTriangle className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <h3 className="font-semibold">{anomaly.title}</h3>
                          <p className="text-sm text-muted-foreground mt-1">
                            {anomaly.description}
                          </p>
                        </div>
                        <Badge variant={STATUS_CONFIG[anomaly.status].color as any} size="sm">
                          {STATUS_CONFIG[anomaly.status].label}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-sm">
                        <div className="flex items-center gap-1">
                          <DirectionIcon className="h-4 w-4" />
                          <span className="font-medium">
                            {anomaly.deviation_percentage !== null && 
                              `${anomaly.deviation_percentage > 0 ? '+' : ''}${anomaly.deviation_percentage.toFixed(1)}%`
                            }
                          </span>
                        </div>
                        <Badge variant={SEVERITY_CONFIG[anomaly.severity].color as any} size="sm">
                          {anomaly.severity}
                        </Badge>
                        <span className="text-muted-foreground">
                          {formatTimeAgo(anomaly.detected_at)}
                        </span>
                        {anomaly.expected_value !== null && (
                          <span className="text-muted-foreground">
                            Expected: {typeof anomaly.expected_value === 'number' && anomaly.expected_value < 1 
                              ? (anomaly.expected_value * 100).toFixed(2) + '%'
                              : formatCurrency(anomaly.expected_value)
                            }
                          </span>
                        )}
                      </div>
                      <div className="mt-3 flex gap-2">
                        <Button size="sm" variant="outline">View Details</Button>
                        {anomaly.status === 'open' && (
                          <Button size="sm" variant="default">Investigate</Button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
