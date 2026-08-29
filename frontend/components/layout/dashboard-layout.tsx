'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Sidebar } from './sidebar';
import { Header } from './header';

interface DashboardLayoutProps {
  children: React.ReactNode;
  className?: string;
  sidebarClassName?: string;
  headerClassName?: string;
  contentClassName?: string;
}

const MOBILE_BREAKPOINT = 1024;

export function DashboardLayout({
  children,
  className,
  sidebarClassName,
  headerClassName,
  contentClassName,
}: DashboardLayoutProps) {
  const [isMobile, setIsMobile] = React.useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(mobile);
      if (mobile) {
        setIsSidebarOpen(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const toggleMobileSidebar = React.useCallback(() => {
    setIsSidebarOpen((prev) => !prev);
  }, []);

  const toggleSidebar = React.useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev);
  }, []);

  return (
    <div
      className={cn(
        'relative flex min-h-screen w-full overflow-hidden bg-background text-foreground',
        className
      )}
    >
      {isMobile && isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={toggleMobileSidebar}
          aria-hidden="true"
        />
      )}

      <div
        className={cn(
          'relative z-40 shrink-0 transition-transform duration-300 ease-in-out',
          isMobile
            ? cn(
                'fixed left-0 top-0 h-screen',
                isSidebarOpen
                  ? 'translate-x-0'
                  : '-translate-x-full'
              )
            : cn(
                'relative h-screen',
                isSidebarCollapsed ? 'translate-x-0' : 'translate-x-0'
              )
        )}
      >
        <Sidebar
          defaultCollapsed={!isMobile && isSidebarCollapsed}
          className={sidebarClassName}
        />
      </div>

      <div className="relative flex min-w-0 flex-1 flex-col">
        <Header
          className={headerClassName}
          onToggleMobileSidebar={toggleMobileSidebar}
          onToggleSidebar={toggleSidebar}
        />

        <main
          id="main-content"
          role="main"
          tabIndex={-1}
          className={cn(
            'relative flex-1 overflow-x-hidden focus-visible:outline-none',
            contentClassName
          )}
        >
          <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 p-4 md:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
