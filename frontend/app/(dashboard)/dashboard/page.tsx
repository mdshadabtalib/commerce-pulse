'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  ShoppingCart,
  Users,
  TrendingUp,
  Package,
  ArrowUpRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import { formatCompactNumber } from '@/lib/utils';
import { useCurrency } from '@/lib/currency-context';
import { KPICard } from '@/components/dashboard/kpi-card';
import { ChartWrapper } from '@/components/dashboard/chart-wrapper';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { SalesKPIs, TimeSeriesPoint, BreakdownItem } from '@/types';

interface DashboardData {
  kpis: SalesKPIs;
  revenue_trend: TimeSeriesPoint[];
  orders_trend: TimeSeriesPoint[];
  product_breakdown: BreakdownItem[];
  customer_segments: BreakdownItem[];
}

export default function DashboardPage() {
  const { formatAmount } = useCurrency();
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: async () => {
      // In production, this would fetch from the API
      // return get<DashboardData>('/analytics/dashboard');
      
      // Mock data for demonstration
      return {
        kpis: {
          total_revenue: 284750.50,
          total_orders: 1845,
          average_order_value: 154.35,
          total_items_sold: 5234,
          net_revenue: 271200.25,
          gross_margin: 0.42,
          discounts_total: 8550.25,
          taxes_total: 22450.00,
          shipping_total: 4500.00,
          refunds_total: 13550.25,
          new_customers: 342,
          returning_customers: 1503,
          conversion_rate: 0.0385,
        },
        revenue_trend: [
          { timestamp: '2024-01-01', date: 'Jan 1', value: 12500, label: 'Jan 1', comparison_value: 11200 },
          { timestamp: '2024-01-02', date: 'Jan 2', value: 13200, label: 'Jan 2', comparison_value: 12100 },
          { timestamp: '2024-01-03', date: 'Jan 3', value: 15800, label: 'Jan 3', comparison_value: 13500 },
          { timestamp: '2024-01-04', date: 'Jan 4', value: 14200, label: 'Jan 4', comparison_value: 13800 },
          { timestamp: '2024-01-05', date: 'Jan 5', value: 16500, label: 'Jan 5', comparison_value: 14200 },
          { timestamp: '2024-01-06', date: 'Jan 6', value: 18200, label: 'Jan 6', comparison_value: 15800 },
          { timestamp: '2024-01-07', date: 'Jan 7', value: 19800, label: 'Jan 7', comparison_value: 17200 },
        ],
        orders_trend: [
          { timestamp: '2024-01-01', date: 'Jan 1', value: 145, label: 'Jan 1' },
          { timestamp: '2024-01-02', date: 'Jan 2', value: 168, label: 'Jan 2' },
          { timestamp: '2024-01-03', date: 'Jan 3', value: 192, label: 'Jan 3' },
          { timestamp: '2024-01-04', date: 'Jan 4', value: 178, label: 'Jan 4' },
          { timestamp: '2024-01-05', date: 'Jan 5', value: 205, label: 'Jan 5' },
          { timestamp: '2024-01-06', date: 'Jan 6', value: 221, label: 'Jan 6' },
          { timestamp: '2024-01-07', date: 'Jan 7', value: 236, label: 'Jan 7' },
        ],
        product_breakdown: [
          { key: 'electronics', label: 'Electronics', value: 125000, percentage: 0.44, color: '#3b82f6' },
          { key: 'clothing', label: 'Clothing', value: 82000, percentage: 0.29, color: '#8b5cf6' },
          { key: 'home', label: 'Home & Garden', value: 45000, percentage: 0.16, color: '#10b981' },
          { key: 'beauty', label: 'Beauty', value: 32750, percentage: 0.11, color: '#f59e0b' },
        ],
        customer_segments: [
          { key: 'vip', label: 'VIP', value: 425, percentage: 0.23, color: '#8b5cf6' },
          { key: 'repeat', label: 'Repeat', value: 1078, percentage: 0.58, color: '#3b82f6' },
          { key: 'at_risk', label: 'At Risk', value: 187, percentage: 0.10, color: '#f59e0b' },
          { key: 'new', label: 'New', value: 155, percentage: 0.09, color: '#10b981' },
        ],
      } as DashboardData;
    },
  });

  if (error) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <div className="text-center">
          <p className="text-sm text-destructive">Failed to load dashboard data</p>
          <p className="text-xs text-muted-foreground mt-1">
            {(error as Error).message}
          </p>
        </div>
      </div>
    );
  }

  const kpis = data?.kpis;
  const revenueTrend = data?.revenue_trend || [];
  const ordersTrend = data?.orders_trend || [];
  const productBreakdown = data?.product_breakdown || [];
  const customerSegments = data?.customer_segments || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your store performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            Last 7 days
          </Button>
          <Button size="sm">
            <ArrowUpRight className="mr-2 h-4 w-4" />
            View Full Report
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Revenue"
          value={formatAmount(kpis?.total_revenue || 0)}
          change={12.5}
          changeLabel="from last period"
          icon={DollarSign}
          trend="up"
          loading={isLoading}
        />
        <KPICard
          title="Total Orders"
          value={formatCompactNumber(kpis?.total_orders || 0)}
          change={8.2}
          changeLabel="from last period"
          icon={ShoppingCart}
          trend="up"
          loading={isLoading}
        />
        <KPICard
          title="Average Order Value"
          value={formatCurrency(kpis?.average_order_value || 0)}
          change={3.1}
          changeLabel="from last period"
          icon={TrendingUp}
          trend="up"
          loading={isLoading}
        />
        <KPICard
          title="Total Items Sold"
          value={formatCompactNumber(kpis?.total_items_sold || 0)}
          change={15.8}
          changeLabel="from last period"
          icon={Package}
          trend="up"
          loading={isLoading}
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="New Customers"
          value={formatCompactNumber(kpis?.new_customers || 0)}
          change={18.5}
          changeLabel="from last period"
          icon={Users}
          trend="up"
          loading={isLoading}
        />
        <KPICard
          title="Returning Customers"
          value={formatCompactNumber(kpis?.returning_customers || 0)}
          change={5.3}
          changeLabel="from last period"
          icon={Users}
          trend="up"
          loading={isLoading}
        />
        <KPICard
          title="Conversion Rate"
          value={`${((kpis?.conversion_rate || 0) * 100).toFixed(2)}%`}
          change={2.4}
          changeLabel="from last period"
          trend="up"
          loading={isLoading}
        />
        <KPICard
          title="Gross Margin"
          value={`${((kpis?.gross_margin || 0) * 100).toFixed(1)}%`}
          change={-1.2}
          changeLabel="from last period"
          trend="down"
          loading={isLoading}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid gap-4 md:grid-cols-2">
        <ChartWrapper
          title="Revenue Trend"
          description="Daily revenue for the last 7 days"
          loading={isLoading}
        >
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={revenueTrend}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="label"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
                tickFormatter={(value) => `$${formatCompactNumber(value)}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => [formatCurrency(value), 'Revenue']}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#colorRevenue)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartWrapper>

        <ChartWrapper
          title="Orders Trend"
          description="Daily orders for the last 7 days"
          loading={isLoading}
        >
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={ordersTrend}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="label"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => [value, 'Orders']}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={{ fill: '#8b5cf6', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartWrapper>
      </div>

      {/* Charts Row 2 */}
      <div className="grid gap-4 md:grid-cols-2">
        <ChartWrapper
          title="Revenue by Category"
          description="Top performing product categories"
          loading={isLoading}
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={productBreakdown} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                type="number"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
                tickFormatter={(value) => `$${formatCompactNumber(value)}`}
              />
              <YAxis
                type="category"
                dataKey="label"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
                width={100}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => [formatCurrency(value), 'Revenue']}
              />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartWrapper>

        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Customer Segments</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex h-[300px] items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              </div>
            ) : (
              <div className="space-y-4">
                {customerSegments.map((segment) => (
                  <div key={segment.key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: segment.color || '#3b82f6' }}
                        />
                        <span className="text-sm font-medium">{segment.label}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">
                          {segment.value.toLocaleString()}
                        </span>
                        <Badge variant="secondary" size="sm">
                          {(segment.percentage * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${segment.percentage * 100}%`,
                          backgroundColor: segment.color || '#3b82f6',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
