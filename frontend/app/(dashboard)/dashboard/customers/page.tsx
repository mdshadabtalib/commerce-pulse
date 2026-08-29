'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  DollarSign,
  ShoppingCart,
  TrendingUp,
  Search,
  Filter,
  Download,
  ChevronRight,
} from 'lucide-react';

import { get } from '@/lib/api';
import { formatCurrency, formatCompactNumber, formatTimeAgo } from '@/lib/utils';
import { KPICard } from '@/components/dashboard/kpi-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import type { CustomerResponse, CustomerSegment } from '@/types';

const SEGMENT_COLORS: Record<CustomerSegment, string> = {
  vip: 'purple',
  repeat: 'info',
  at_risk: 'warning',
  one_time: 'secondary',
  new: 'success',
};

export default function CustomersPage() {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedSegment, setSelectedSegment] = React.useState<CustomerSegment | 'all'>('all');

  const { data, isLoading } = useQuery({
    queryKey: ['customers', 'list', searchTerm, selectedSegment],
    queryFn: async () => {
      // Mock data - in production this would call the API
      return {
        kpis: {
          total_customers: 8942,
          growth: 0.145,
          avg_lifetime_value: 1247.35,
          ltv_growth: 0.082,
          avg_order_value: 284.50,
          aov_growth: 0.034,
          repeat_rate: 0.62,
          repeat_growth: 0.028,
        },
        segments: [
          { segment: 'vip', count: 892, percentage: 10, avg_ltv: 4250 },
          { segment: 'repeat', count: 4695, percentage: 52.5, avg_ltv: 1580 },
          { segment: 'at_risk', count: 1342, percentage: 15, avg_ltv: 890 },
          { segment: 'one_time', count: 1563, percentage: 17.5, avg_ltv: 285 },
          { segment: 'new', count: 450, percentage: 5, avg_ltv: 320 },
        ],
        customers: [
          {
            id: '1',
            email: 'sarah.chen@example.com',
            full_name: 'Sarah Chen',
            avatar_url: null,
            segment: 'vip' as CustomerSegment,
            orders_count: 48,
            total_spent: 12450.75,
            average_order_value: 259.39,
            lifetime_value: 12450.75,
            last_order_at: '2024-01-28T10:30:00Z',
            first_order_at: '2022-03-15T14:20:00Z',
            days_since_last_order: 2,
            created_at: '2022-03-15T14:20:00Z',
          },
          {
            id: '2',
            email: 'michael.rodriguez@example.com',
            full_name: 'Michael Rodriguez',
            avatar_url: null,
            segment: 'repeat' as CustomerSegment,
            orders_count: 12,
            total_spent: 3240.50,
            average_order_value: 270.04,
            lifetime_value: 3240.50,
            last_order_at: '2024-01-25T16:45:00Z',
            first_order_at: '2023-06-10T09:15:00Z',
            days_since_last_order: 5,
            created_at: '2023-06-10T09:15:00Z',
          },
          {
            id: '3',
            email: 'emily.watson@example.com',
            full_name: 'Emily Watson',
            avatar_url: null,
            segment: 'at_risk' as CustomerSegment,
            orders_count: 8,
            total_spent: 1890.25,
            average_order_value: 236.28,
            lifetime_value: 1890.25,
            last_order_at: '2023-11-15T12:00:00Z',
            first_order_at: '2023-02-20T10:30:00Z',
            days_since_last_order: 76,
            created_at: '2023-02-20T10:30:00Z',
          },
          {
            id: '4',
            email: 'david.kim@example.com',
            full_name: 'David Kim',
            avatar_url: null,
            segment: 'repeat' as CustomerSegment,
            orders_count: 15,
            total_spent: 4567.80,
            average_order_value: 304.52,
            lifetime_value: 4567.80,
            last_order_at: '2024-01-27T08:20:00Z',
            first_order_at: '2023-04-12T11:45:00Z',
            days_since_last_order: 3,
            created_at: '2023-04-12T11:45:00Z',
          },
          {
            id: '5',
            email: 'jessica.brown@example.com',
            full_name: 'Jessica Brown',
            avatar_url: null,
            segment: 'new' as CustomerSegment,
            orders_count: 2,
            total_spent: 345.90,
            average_order_value: 172.95,
            lifetime_value: 345.90,
            last_order_at: '2024-01-26T14:10:00Z',
            first_order_at: '2024-01-20T16:30:00Z',
            days_since_last_order: 4,
            created_at: '2024-01-20T16:30:00Z',
          },
        ] as CustomerResponse[],
      };
    },
  });

  const kpis = data?.kpis;
  const customers = data?.customers || [];
  const segments = data?.segments || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Customers</h1>
          <p className="text-muted-foreground mt-1">
            Manage and analyze your customer base
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Filter className="mr-2 h-4 w-4" />
            Filters
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Customers"
          value={formatCompactNumber(kpis?.total_customers || 0)}
          change={(kpis?.growth || 0) * 100}
          changeLabel="vs previous period"
          icon={Users}
          trend={kpis?.growth && kpis.growth > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
        <KPICard
          title="Avg Lifetime Value"
          value={formatCurrency(kpis?.avg_lifetime_value || 0)}
          change={(kpis?.ltv_growth || 0) * 100}
          changeLabel="vs previous period"
          icon={DollarSign}
          trend={kpis?.ltv_growth && kpis.ltv_growth > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
        <KPICard
          title="Avg Order Value"
          value={formatCurrency(kpis?.avg_order_value || 0)}
          change={(kpis?.aov_growth || 0) * 100}
          changeLabel="vs previous period"
          icon={ShoppingCart}
          trend={kpis?.aov_growth && kpis.aov_growth > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
        <KPICard
          title="Repeat Purchase Rate"
          value={`${((kpis?.repeat_rate || 0) * 100).toFixed(1)}%`}
          change={(kpis?.repeat_growth || 0) * 100}
          changeLabel="vs previous period"
          icon={TrendingUp}
          trend={kpis?.repeat_growth && kpis.repeat_growth > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
      </div>

      {/* Customer Segments */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Segments</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-[150px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-5">
              {segments.map((seg) => (
                <button
                  key={seg.segment}
                  onClick={() => setSelectedSegment(seg.segment as CustomerSegment)}
                  className={`rounded-lg border p-4 text-left transition-all hover:shadow-md ${
                    selectedSegment === seg.segment
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                      : 'border-border'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant={SEGMENT_COLORS[seg.segment as CustomerSegment] as any} size="sm">
                      {seg.segment.replace('_', ' ')}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{seg.percentage}%</span>
                  </div>
                  <div className="text-2xl font-bold">{seg.count.toLocaleString()}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {formatCurrency(seg.avg_ltv)} avg LTV
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Customer List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Customer List</CardTitle>
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search customers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-[400px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="space-y-3">
              {customers.map((customer) => (
                <div
                  key={customer.id}
                  className="flex items-center justify-between rounded-lg border border-border p-4 transition-all hover:shadow-md hover:border-primary/50 cursor-pointer"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={customer.avatar_url || undefined} />
                      <AvatarFallback className="bg-primary/10 text-primary">
                        {customer.full_name?.charAt(0) || customer.email?.charAt(0) || '?'}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium truncate">{customer.full_name || customer.email}</p>
                        <Badge variant={SEGMENT_COLORS[customer.segment as CustomerSegment] as any} size="sm">
                          {customer.segment?.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">{customer.email}</p>
                    </div>
                  </div>

                  <div className="hidden md:flex items-center gap-8">
                    <div className="text-right">
                      <div className="text-sm font-medium">{customer.orders_count} orders</div>
                      <div className="text-xs text-muted-foreground">
                        {formatTimeAgo(customer.last_order_at || '')}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{formatCurrency(customer.total_spent)}</div>
                      <div className="text-xs text-muted-foreground">Total spent</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{formatCurrency(customer.average_order_value)}</div>
                      <div className="text-xs text-muted-foreground">AOV</div>
                    </div>
                    <Button variant="ghost" size="icon">
                      <ChevronRight className="h-5 w-5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
