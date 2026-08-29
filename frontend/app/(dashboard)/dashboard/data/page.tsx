'use client';

import * as React from 'react';
import { useQuery } from '@tantml:react-query';
import { Database, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';

import { formatTimeAgo, formatCompactNumber } from '@/lib/utils';
import { KPICard } from '@/components/dashboard/kpi-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { Dataset } from '@/types';

export default function DataPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['datasets', 'list'],
    queryFn: async () => {
      return {
        kpis: {
          total_datasets: 5,
          active: 4,
          syncing: 1,
          total_records: 145820,
        },
        datasets: [
          {
            id: '1',
            name: 'Shopify Store - Main',
            source_type: 'shopify' as const,
            status: 'ready' as const,
            records_count: 98450,
            last_synced_at: '2024-01-28T10:30:00Z',
            next_sync_at: '2024-01-28T22:30:00Z',
            sync_frequency_minutes: 720,
            is_active: true,
            created_at: '2023-01-15T09:00:00Z',
          },
          {
            id: '2',
            name: 'Amazon Seller Central',
            source_type: 'amazon' as const,
            status: 'ready' as const,
            records_count: 34280,
            last_synced_at: '2024-01-28T08:15:00Z',
            next_sync_at: '2024-01-28T20:15:00Z',
            sync_frequency_minutes: 720,
            is_active: true,
            created_at: '2023-03-20T14:30:00Z',
          },
          {
            id: '3',
            name: 'Stripe Payments',
            source_type: 'stripe' as const,
            status: 'importing' as const,
            records_count: 12340,
            last_synced_at: '2024-01-28T12:00:00Z',
            next_sync_at: null,
            sync_frequency_minutes: 60,
            is_active: true,
            created_at: '2023-02-10T11:45:00Z',
          },
          {
            id: '4',
            name: 'WooCommerce - EU Store',
            source_type: 'woocommerce' as const,
            status: 'ready' as const,
            records_count: 750,
            last_synced_at: '2024-01-28T06:00:00Z',
            next_sync_at: '2024-01-29T06:00:00Z',
            sync_frequency_minutes: 1440,
            is_active: true,
            created_at: '2023-11-05T16:20:00Z',
          },
        ] as Dataset[],
      };
    },
  });

  const kpis = data?.kpis;
  const datasets = data?.datasets || [];

  const statusConfig = {
    ready: { icon: CheckCircle, color: 'success', label: 'Ready' },
    importing: { icon: RefreshCw, color: 'info', label: 'Syncing' },
    failed: { icon: XCircle, color: 'destructive', label: 'Failed' },
    pending: { icon: Clock, color: 'warning', label: 'Pending' },
    disabled: { icon: XCircle, color: 'secondary', label: 'Disabled' },
    archived: { icon: XCircle, color: 'secondary', label: 'Archived' },
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Sources</h1>
          <p className="text-muted-foreground mt-1">
            Manage your connected integrations and data sync
          </p>
        </div>
        <Button>
          <Database className="mr-2 h-4 w-4" />
          Connect Data Source
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <KPICard
          title="Total Sources"
          value={kpis?.total_datasets || 0}
          icon={Database}
          loading={isLoading}
        />
        <KPICard
          title="Active"
          value={kpis?.active || 0}
          icon={CheckCircle}
          loading={isLoading}
        />
        <KPICard
          title="Syncing"
          value={kpis?.syncing || 0}
          icon={RefreshCw}
          loading={isLoading}
        />
        <KPICard
          title="Total Records"
          value={formatCompactNumber(kpis?.total_records || 0)}
          icon={Database}
          loading={isLoading}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connected Sources</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-[400px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="space-y-4">
              {datasets.map((dataset) => {
                const StatusIcon = statusConfig[dataset.status]?.icon || Clock;
                return (
                  <div
                    key={dataset.id}
                    className="flex items-center justify-between rounded-lg border border-border p-4 transition-all hover:shadow-md"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="p-3 rounded-lg bg-primary/10">
                        <Database className="h-6 w-6 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{dataset.name}</h3>
                          <Badge variant={statusConfig[dataset.status]?.color as any} size="sm" className="gap-1">
                            <StatusIcon className="h-3 w-3" />
                            {statusConfig[dataset.status]?.label}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {formatCompactNumber(dataset.records_count || 0)} records • 
                          Last synced {formatTimeAgo(dataset.last_synced_at || '')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        Settings
                      </Button>
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
