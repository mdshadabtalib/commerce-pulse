'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import * as React from 'react';
import {
  Building2,
  ChevronDown,
  LogOut,
  Moon,
  Search,
  Settings,
  Sun,
  UserCircle,
  User as UserIcon,
  Bell,
  DollarSign,
  Menu,
  PanelLeft,
  type LucideIcon,
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { cn, getInitials } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface OrganizationOption {
  id: string | number;
  name: string;
  slug?: string;
  logo?: string;
  plan?: string;
}

interface UserDropdownProps {
  user?: {
    id?: string | number;
    full_name: string;
    email: string;
    avatar_url?: string | null;
  };
  organizations?: OrganizationOption[];
  currentOrg?: OrganizationOption;
}

const CURRENCIES: { code: string; symbol: string; label: string }[] = [
  { code: 'USD', symbol: '$', label: 'US Dollar' },
  { code: 'EUR', symbol: '€', label: 'Euro' },
  { code: 'GBP', symbol: '£', label: 'British Pound' },
  { code: 'JPY', symbol: '¥', label: 'Japanese Yen' },
  { code: 'CAD', symbol: 'C$', label: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', label: 'Australian Dollar' },
  { code: 'SGD', symbol: 'S$', label: 'Singapore Dollar' },
];

const DEFAULT_ORGS: OrganizationOption[] = [
  { id: 1, name: 'Acme Commerce', slug: 'acme', plan: 'Growth' },
];

const DEFAULT_USER = {
  full_name: 'Jane Cooper',
  email: 'jane@acmecommerce.com',
};

function UserAvatar({
  user,
  className,
}: {
  user?: { full_name: string; avatar_url?: string | null };
  className?: string;
}) {
  const name = user?.full_name || 'User';
  return (
    <div
      className={cn(
        'relative inline-flex h-9 w-9 items-center justify-center overflow-hidden rounded-full bg-primary text-primary-foreground text-sm font-semibold',
        className
      )}
    >
      {user?.avatar_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={user.avatar_url}
          alt={name}
          className="h-full w-full object-cover"
        />
      ) : (
        getInitials(name)
      )}
    </div>
  );
}

export function Header({
  user = DEFAULT_USER,
  organizations = DEFAULT_ORGS,
  currentOrg,
  onToggleMobileSidebar,
  onToggleSidebar,
  className,
  ...props
}: UserDropdownProps &
  React.HTMLAttributes<HTMLElement> & {
    onToggleMobileSidebar?: () => void;
    onToggleSidebar?: () => void;
  }) {
  const router = useRouter();
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  const [currency, setCurrency] = React.useState<string>(
    process.env.NEXT_PUBLIC_CURRENCY_DEFAULT || 'USD'
  );
  const [notifCount] = React.useState<number>(3);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const activeOrg = currentOrg || organizations[0];
  const currentCurrency = CURRENCIES.find((c) => c.code === currency) || CURRENCIES[0];

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
    router.push('/login');
  };

  const toggleTheme = () => {
    const nextTheme =
      mounted && (resolvedTheme === 'dark' || theme === 'dark')
        ? 'light'
        : 'dark';
    setTheme(nextTheme);
  };

  return (
    <header
      className={cn(
        'sticky top-0 z-40 h-16 w-full border-b border-border bg-background/80 backdrop-blur-xl',
        className
      )}
      {...props}
    >
      <div className="flex h-full items-center gap-3 px-4 lg:px-6">
        <div className="flex items-center gap-1 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleMobileSidebar}
            aria-label="Toggle mobile menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>

        <div className="hidden md:block">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <PanelLeft className="h-5 w-5" />
          </Button>
        </div>

        <div className="hidden flex-1 items-center gap-3 md:flex md:max-w-md lg:max-w-lg">
          <div className="relative w-full">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              placeholder="Search orders, products, customers..."
              className="flex h-10 w-full items-center gap-2 rounded-lg border border-input bg-background/50 pl-9 pr-16 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
            />
            <kbd className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 select-none items-center gap-1 rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] font-medium text-muted-foreground md:inline-flex">
              <span className="text-xs">⌘</span>K
            </kbd>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-end gap-1 md:hidden">
          <Button variant="ghost" size="icon" aria-label="Search">
            <Search className="h-5 w-5" />
          </Button>
        </div>

        <div className="ml-auto flex items-center gap-1 md:gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="flex items-center gap-2 h-9 px-2 md:px-3"
              >
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Building2 className="h-4 w-4" />
                </div>
                <span className="hidden min-w-0 max-w-[120px] truncate text-sm font-medium sm:inline-block">
                  {activeOrg?.name}
                </span>
                {activeOrg?.plan && (
                  <Badge
                    variant="outline"
                    size="sm"
                    className="hidden shrink-0 border-primary/20 bg-primary/5 text-primary lg:inline-flex"
                  >
                    {activeOrg.plan}
                  </Badge>
                )}
                <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72">
              <DropdownMenuLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Organizations
              </DropdownMenuLabel>
              {organizations.map((org) => (
                <DropdownMenuItem
                  key={org.id}
                  className="cursor-pointer gap-3"
                  onClick={() => router.push(`/org/${org.slug || org.id}`)}
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <Building2 className="h-4 w-4" />
                  </div>
                  <div className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate text-sm font-medium">
                      {org.name}
                    </span>
                    {org.plan && (
                      <span className="truncate text-xs text-muted-foreground">
                        {org.plan} plan
                      </span>
                    )}
                  </div>
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="cursor-pointer gap-3 text-muted-foreground hover:text-foreground"
                onClick={() => router.push('/onboarding/org')}
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                  <span className="text-base leading-none">+</span>
                </div>
                <span className="text-sm font-medium">Create organization</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9"
                aria-label="Select currency"
              >
                <DollarSign className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Display Currency
              </DropdownMenuLabel>
              {CURRENCIES.map((cur) => (
                <DropdownMenuItem
                  key={cur.code}
                  className="cursor-pointer justify-between"
                  onClick={() => setCurrency(cur.code)}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-muted-foreground">
                      {cur.symbol}
                    </span>
                    <span className="text-sm">{cur.label}</span>
                  </div>
                  {cur.code === currency && (
                    <span className="text-xs text-primary font-medium">
                      ✓
                    </span>
                  )}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-9 w-9"
            aria-label="Toggle theme"
          >
            {mounted && (resolvedTheme === 'dark' || theme === 'dark') ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="relative h-9 w-9"
            aria-label="Notifications"
            onClick={() => router.push('/dashboard/notifications')}
          >
            <Bell className="h-5 w-5" />
            {notifCount > 0 && (
              <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground ring-2 ring-background">
                {notifCount > 99 ? '99+' : notifCount}
              </span>
            )}
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-9 shrink-0 gap-2 px-1 pr-2"
              >
                <UserAvatar user={user} />
                <span className="hidden min-w-0 max-w-[110px] truncate text-sm font-medium lg:inline-block">
                  {user.full_name.split(' ')[0]}
                </span>
                <ChevronDown className="hidden h-4 w-4 text-muted-foreground lg:block" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuLabel className="p-3">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-3">
                    <UserAvatar user={user} className="h-10 w-10" />
                    <div className="flex min-w-0 flex-col">
                      <span className="truncate text-sm font-semibold text-foreground">
                        {user.full_name}
                      </span>
                      <span className="truncate text-xs text-muted-foreground">
                        {user.email}
                      </span>
                    </div>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem
                  className="gap-3 cursor-pointer"
                  onClick={() => router.push('/dashboard/profile')}
                >
                  <UserIcon className="h-4 w-4" />
                  <span>Profile</span>
                  <DropdownMenuShortcut>⇧⌘P</DropdownMenuShortcut>
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="gap-3 cursor-pointer"
                  onClick={() => router.push('/dashboard/settings')}
                >
                  <Settings className="h-4 w-4" />
                  <span>Settings</span>
                  <DropdownMenuShortcut>⌘,</DropdownMenuShortcut>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="gap-3 cursor-pointer text-destructive focus:text-destructive"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4" />
                <span>Log out</span>
                <DropdownMenuShortcut>⇧⌘Q</DropdownMenuShortcut>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}

export { UserAvatar };
