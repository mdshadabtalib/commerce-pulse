import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ChartWrapperProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  loading?: boolean;
  action?: React.ReactNode;
}

export function ChartWrapper({
  title,
  description,
  children,
  className,
  loading,
  action,
}: ChartWrapperProps) {
  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle className="text-base font-semibold">{title}</CardTitle>
          {description && (
            <CardDescription className="text-xs">{description}</CardDescription>
          )}
        </div>
        {action && <div className="flex items-center gap-2">{action}</div>}
      </CardHeader>
      <CardContent className="pt-4">
        {loading ? (
          <div className="flex h-[300px] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}
