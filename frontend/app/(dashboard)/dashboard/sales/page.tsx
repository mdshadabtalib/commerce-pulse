'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  TrendingUp,
  ShoppingBag,
  Percent,
  Calendar,
  Download,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

import { formatCurrency, formatCompactNumber } from '@/lib/utils';
import { KPICard } from '@/components/dashboard/kpi-card';
import { ChartWrapper } from '@/components/dashboard/chart-wrapper';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function SalesPage() {
  const [dateRange, setDateRange] = React.useState('30d');
  const [compareEnabled, setCompareEnabled] = React.useState(true);

  const { data, isLoading } = useQuery({
    queryKey: ['sales', 'analytics', dateRange],
    queryFn: async () => {
      // Mock data - in production this would call the API
      return {
        kpis: {
          total_revenue: 847250.75,
          growth_rate: 0.185,
          total_orders: 3284,
          orders_growth: 0.124,
          average_order_value: 258.12,
          aov_growth: 0.055,
          conversion_rate: 0.0428,
          conversion_growth: 0.032,
        },
        revenue_by_day: Array.from({ length: 30 }, (_, i) => ({
          date: `Day ${i + 1}`,
          revenue: 25000 + Math.random() * 15000,
          previous: 22000 + Math.random() * 12000,
        })),
        revenue_by_channel: [
          { name: 'Direct', value: 342500, percentage: 40.4, color: '#3b82f6' },
          { name: 'Organic Search', value: 254175, percentage: 30.0, color: '#8b5cf6' },
          { name: 'Paid Ads', value: 152415, percentage: 18.0, color: '#10b981' },
          { name: 'Social Media', value: 76363, percentage: 9.0, color: '#f59e0b' },
          { name: 'Email', value: 21818, percentage: 2.6, color: '#ef4444' },
        ],
        revenue_by_category: [
          { category: 'Electronics', revenue: 285420, orders: 1142, aov: 250 },
          { category: 'Clothing', revenue: 234180, orders: 1845, aov: 127 },
          { category: 'Home & Garden', revenue: 165290, orders: 634, aov: 261 },
          { category: 'Beauty', revenue: 98320, orders: 487, aov: 202 },
          { category: 'Sports', revenue: 64040, orders: 176, aov: 364 },
        ],
        hourly_pattern: Array.from({ length: 24 }, (_, i) => ({
          hour: `${i}:00`,
          orders: Math.floor(50 + Math.random() * 150 + Math.sin(i / 4) * 50),
        })),
      };
    },
  });

  const kpis = data?.kpis;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sales Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Deep dive into revenue performance and trends
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-[180px]">
              <Calendar className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Revenue"
          value={formatCurrency(kpis?.total_revenue || 0)}
          change={(kpis?.growth_rate || 0) * 100}
          changeLabel="vs previous period"
          icon={DollarSign}
          trend={kpis?.growth_rate && kpis.growth_rate > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
        <KPICard
          title="Total Orders"
          value={formatCompactNumber(kpis?.total_orders || 0)}
          change={(kpis?.orders_growth || 0) * 100}
          changeLabel="vs previous period"
          icon={ShoppingBag}
          trend={kpis?.orders_growth && kpis.orders_growth > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
        <KPICard
          title="Average Order Value"
          value={formatCurrency(kpis?.average_order_value || 0)}
          change={(kpis?.aov_growth || 0) * 100}
          changeLabel="vs previous period"
          icon={TrendingUp}
          trend={kpis?.aov_growth && kpis.aov_growth > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
        <KPICard
          title="Conversion Rate"
          value={`${((kpis?.conversion_rate || 0) * 100).toFixed(2)}%`}
          change={(kpis?.conversion_growth || 0) * 100}
          changeLabel="vs previous period"
          icon={Percent}
          trend={kpis?.conversion_growth && kpis.conversion_growth > 0 ? 'up' : 'down'}
          loading={isLoading}
        />
      </div>

      {/* Revenue Trend */}
      <ChartWrapper
        title="Revenue Over Time"
        description="Daily revenue with period comparison"
        loading={isLoading}
        action={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCompareEnabled(!compareEnabled)}
          >
            {compareEnabled ? 'Hide' : 'Show'} Comparison
          </Button>
        }
      >
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data?.revenue_by_day || []}>
            <defs>
              <linearGradient id="colorCurrent" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorPrevious" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
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
              formatter={(value: number) => formatCurrency(value)}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="revenue"
              name="Current Period"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#colorCurrent)"
            />
            {compareEnabled && (
              <Area
                type="monotone"
                dataKey="previous"
                name="Previous Period"
                stroke="#94a3b8"
                strokeWidth={2}
                strokeDasharray="5 5"
                fill="url(#colorPrevious)"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </ChartWrapper>

      {/* Revenue Breakdown */}
      <div className="grid gap-4 md:grid-cols-2">
        <ChartWrapper
          title="Revenue by Channel"
          description="Traffic source performance"
          loading={isLoading}
        >
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data?.revenue_by_channel || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name} ${entry.percentage}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {(data?.revenue_by_channel || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => formatCurrency(value)}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartWrapper>

        <ChartWrapper
          title="Revenue by Category"
          description="Top performing product categories"
          loading={isLoading}
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data?.revenue_by_category || []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                type="number"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
                tickFormatter={(value) => `$${formatCompactNumber(value)}`}
              />
              <YAxis
                type="category"
                dataKey="category"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
                width={120}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => formatCurrency(value)}
              />
              <Bar dataKey="revenue" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartWrapper>
      </div>

      {/* Hourly Pattern */}
      <ChartWrapper
        title="Order Volume by Hour"
        description="24-hour order pattern analysis"
        loading={isLoading}
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data?.hourly_pattern || []}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="hour"
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
            />
            <Line
              type="monotone"
              dataKey="orders"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: '#10b981', r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartWrapper>

      {/* Category Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Category Performance</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-[200px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border text-left text-sm text-muted-foreground">
                    <th className="pb-3 font-medium">Category</th>
                    <th className="pb-3 font-medium text-right">Revenue</th>
                    <th className="pb-3 font-medium text-right">Orders</th>
                    <th className="pb-3 font-medium text-right">AOV</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.revenue_by_category || []).map((category) => (
                    <tr key={category.category} className="border-b border-border/50 last:border-0">
                      <td className="py-3 font-medium">{category.category}</td>
                      <td className="py-3 text-right">{formatCurrency(category.revenue)}</td>
                      <td className="py-3 text-right">{category.orders.toLocaleString()}</td>
                      <td className="py-3 text-right">{formatCurrency(category.aov)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
