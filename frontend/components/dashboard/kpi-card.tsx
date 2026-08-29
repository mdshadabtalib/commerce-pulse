import * as React from 'react';
import { ArrowDown, ArrowUp, Minus, TrendingUp, TrendingDown, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: LucideIcon;
  trend?: 'up' | 'down' | 'flat';
  loading?: boolean;
  className?: string;
  description?: string;
  badge?: string;
  badgeVariant?: 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'info';
}

export function KPICard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  trend,
  loading,
  className,
  description,
  badge,
  badgeVariant = 'default',
}: KPICardProps) {
  const changeIsPositive = change !== undefined && change > 0;
  const changeIsNegative = change !== undefined && change < 0;
  const changeIsNeutral = change !== undefined && change === 0;

  const trendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const TrendIcon = trendIcon;

  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {Icon && (
          <Icon className="h-4 w-4 text-muted-foreground" />
        )}
        {badge && (
          <Badge variant={badgeVariant} size="sm">
            {badge}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <div className="h-8 w-24 animate-pulse rounded bg-muted" />
            <div className="h-4 w-16 animate-pulse rounded bg-muted" />
          </div>
        ) : (
          <>
            <div className="flex items-baseline gap-2">
              <div className="text-2xl font-bold">{value}</div>
              {trend && (
                <TrendIcon
                  className={cn(
                    'h-4 w-4',
                    trend === 'up' && 'text-emerald-500',
                    trend === 'down' && 'text-red-500',
                    trend === 'flat' && 'text-muted-foreground'
                  )}
                />
              )}
            </div>

            {(change !== undefined || changeLabel) && (
              <div className="flex items-center gap-1 text-xs">
                {change !== undefined && (
                  <>
                    {changeIsPositive && (
                      <ArrowUp className="h-3 w-3 text-emerald-500" />
                    )}
                    {changeIsNegative && (
                      <ArrowDown className="h-3 w-3 text-red-500" />
                    )}
                    {changeIsNeutral && (
                      <Minus className="h-3 w-3 text-muted-foreground" />
                    )}
                    <span
                      className={cn(
                        'font-medium',
                        changeIsPositive && 'text-emerald-600 dark:text-emerald-500',
                        changeIsNegative && 'text-red-600 dark:text-red-500',
                        changeIsNeutral && 'text-muted-foreground'
                      )}
                    >
                      {changeIsPositive && '+'}
                      {Math.abs(change).toFixed(1)}%
                    </span>
                  </>
                )}
                {changeLabel && (
                  <span className="text-muted-foreground">{changeLabel}</span>
                )}
              </div>
            )}

            {description && (
              <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
