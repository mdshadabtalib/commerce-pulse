'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Target, Zap, AlertCircle } from 'lucide-react';
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';

import { formatCurrency, formatCompactNumber } from '@/lib/utils';
import { KPICard } from '@/components/dashboard/kpi-card';
import { ChartWrapper } from '@/components/dashboard/chart-wrapper';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function ForecastingPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['forecasting', 'revenue'],
    queryFn: async () => {
      return {
        kpis: {
          next_30_days_forecast: 925400,
          confidence: 0.94,
          accuracy: 0.91,
          trend: 'up' as const,
        },
        forecast_data: Array.from({ length: 60 }, (_, i) => {
          const isHistorical = i < 30;
          const baseValue = 28000 + Math.sin(i / 5) * 5000;
          return {
            date: `Day ${i + 1}`,
            actual: isHistorical ? baseValue + (Math.random() - 0.5) * 2000 : null,
            predicted: !isHistorical ? baseValue * 1.1 + (Math.random() - 0.5) * 1000 : null,
            lower_bound: !isHistorical ? baseValue * 1.05 : null,
            upper_bound: !isHistorical ? baseValue * 1.15 : null,
          };
        }),
      };
    },
  });

  const kpis = data?.kpis;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h1 className="text-3xl font-bold tracking-tight">AI Forecasting</h1>
          <Badge variant="purple" className="gap-1">
            <Zap className="h-3 w-3" />
            AI Powered
          </Badge>
        </div>
        <p className="text-muted-foreground">
          ML-powered demand predictions with confidence intervals
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <KPICard
          title="30-Day Forecast"
          value={formatCurrency(kpis?.next_30_days_forecast || 0)}
          icon={TrendingUp}
          trend={kpis?.trend}
          badge="Next 30 days"
          badgeVariant="info"
          loading={isLoading}
        />
        <KPICard
          title="Model Confidence"
          value={`${((kpis?.confidence || 0) * 100).toFixed(0)}%`}
          icon={Target}
          description="95% confidence interval"
          loading={isLoading}
        />
        <KPICard
          title="Historical Accuracy"
          value={`${((kpis?.accuracy || 0) * 100).toFixed(1)}%`}
          icon={TrendingUp}
          description="MAPE on test set"
          loading={isLoading}
        />
      </div>

      <ChartWrapper
        title="Revenue Forecast"
        description="Historical actuals and 30-day predictions"
        loading={isLoading}
      >
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data?.forecast_data || []}>
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorBounds" x1="0" y1="0" x2="0" y2="1">
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
              formatter={(value: number | null) => value !== null ? formatCurrency(value) : 'N/A'}
            />
            <Legend />
            <ReferenceLine x="Day 30" stroke="#ef4444" strokeDasharray="3 3" label="Today" />
            <Area
              type="monotone"
              dataKey="upper_bound"
              stroke="none"
              fill="url(#colorBounds)"
              fillOpacity={0.3}
              name="Upper Bound"
            />
            <Area
              type="monotone"
              dataKey="lower_bound"
              stroke="none"
              fill="url(#colorBounds)"
              fillOpacity={0.3}
              name="Lower Bound"
            />
            <Area
              type="monotone"
              dataKey="actual"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#colorActual)"
              name="Actual"
            />
            <Area
              type="monotone"
              dataKey="predicted"
              stroke="#8b5cf6"
              strokeWidth={2}
              strokeDasharray="5 5"
              fill="url(#colorPredicted)"
              name="Predicted"
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartWrapper>

      <Card>
        <CardHeader>
          <CardTitle>Forecast Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
              <TrendingUp className="h-5 w-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">Strong upward trend detected</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Revenue is projected to increase by 12.5% over the next 30 days based on historical patterns and seasonality.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
              <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <p className="font-medium">Model retraining recommended</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Accuracy has decreased by 2.3% in the last week. Consider retraining with recent data to improve predictions.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
