'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import * as React from 'react';
import {
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  ShoppingCart,
  Users,
  Package,
  Boxes,
  TrendingUp,
  AlertTriangle,
  FileBarChart,
  Database,
  Plug,
  Settings,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { cn, getInitials } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  badge?: string | number;
  badgeVariant?:
    | 'default'
    | 'secondary'
    | 'destructive'
    | 'outline'
    | 'success'
    | 'warning'
    | 'info'
    | 'purple';
}

const MAIN_NAV: NavItem[] = [
  {
    title: 'Overview',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Sales',
    href: '/dashboard/sales',
    icon: ShoppingCart,
  },
  {
    title: 'Customers',
    href: '/dashboard/customers',
    icon: Users,
  },
  {
    title: 'Products',
    href: '/dashboard/products',
    icon: Package,
  },
  {
    title: 'Inventory',
    href: '/dashboard/inventory',
    icon: Boxes,
  },
  {
    title: 'Forecasting',
    href: '/dashboard/forecasting',
    icon: TrendingUp,
    badge: 'AI',
    badgeVariant: 'purple',
  },
  {
    title: 'Anomalies',
    href: '/dashboard/anomalies',
    icon: AlertTriangle,
    badgeVariant: 'destructive',
  },
  {
    title: 'Reports',
    href: '/dashboard/reports',
    icon: FileBarChart,
  },
  {
    title: 'Data',
    href: '/dashboard/data',
    icon: Database,
  },
  {
    title: 'Integrations',
    href: '/dashboard/integrations',
    icon: Plug,
  },
  {
    title: 'Settings',
    href: '/dashboard/settings',
    icon: Settings,
  },
];

interface SidebarProps
  extends React.HTMLAttributes<HTMLElement> {
  defaultCollapsed?: boolean;
}

export function Sidebar({
  className,
  defaultCollapsed = false,
  ...props
}: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed);

  const toggleCollapsed = React.useCallback(() => {
    setCollapsed((prev) => !prev);
  }, []);

  return (
    <aside
      data-collapsed={collapsed}
      className={cn(
        'group/sidebar-wrapper relative flex h-full flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out',
        collapsed ? 'w-[72px]' : 'w-72',
        className
      )}
      {...props}
    >
      <div className="flex h-16 items-center justify-between gap-2 border-b border-sidebar-border px-4 shrink-0">
        <Link
          href="/dashboard"
          className={cn(
            'flex items-center gap-2 overflow-hidden transition-all duration-200',
            collapsed ? 'justify-center w-full' : ''
          )}
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Sparkles className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col leading-tight whitespace-nowrap">
              <span className="text-base font-bold tracking-tight text-sidebar-foreground">
                {process.env.NEXT_PUBLIC_APP_NAME || 'CommercePulse'}
              </span>
            </div>
          )}
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden px-3 py-4">
        <nav className="flex flex-col gap-1">
          {MAIN_NAV.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === '/dashboard'
                ? pathname === '/dashboard'
                : pathname?.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                title={collapsed ? item.title : undefined}
                className={cn(
                  'group relative flex h-10 min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors duration-200',
                  collapsed ? 'justify-center px-2' : '',
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'
                )}
              >
                {isActive && !collapsed && (
                  <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-r bg-primary" />
                )}
                <Icon
                  className={cn(
                    'shrink-0 transition-all duration-200',
                    isActive ? 'text-primary' : '',
                    collapsed ? 'h-5 w-5' : 'h-5 w-5'
                  )}
                />
                {!collapsed && (
                  <>
                    <span className="flex-1 truncate whitespace-nowrap">
                      {item.title}
                    </span>
                    {item.badge !== undefined && (
                      <Badge
                        variant={item.badgeVariant || 'default'}
                        size="sm"
                      >
                        {item.badge}
                      </Badge>
                    )}
                  </>
                )}
                {collapsed && item.badge !== undefined && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/60 opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="shrink-0 border-t border-sidebar-border p-3">
        <button
          type="button"
          onClick={toggleCollapsed}
          className="flex h-9 w-full items-center justify-center gap-2 rounded-lg text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span className="text-xs font-medium">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

export function SidebarUser({
  user,
  className,
}: {
  user?: {
    name: string;
    email?: string;
    avatar?: string;
  };
  className?: string;
}) {
  const name = user?.name || 'User';
  const email = user?.email || 'user@example.com';
  const avatar = user?.avatar;

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg bg-sidebar-accent p-2.5',
        className
      )}
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-semibold">
        {avatar ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={avatar}
            alt={name}
            className="h-full w-full rounded-full object-cover"
          />
        ) : (
          getInitials(name)
        )}
      </div>
      <div className="flex min-w-0 flex-col">
        <span className="truncate text-sm font-medium text-sidebar-accent-foreground">
          {name}
        </span>
        <span className="truncate text-xs text-sidebar-foreground/60">
          {email}
        </span>
      </div>
    </div>
  );
}
