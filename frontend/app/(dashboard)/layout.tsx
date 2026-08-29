'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'sonner';

import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { useAuth } from '@/lib/auth';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, isAuthenticated, loading } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false);

  React.useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen overflow-hidden bg-background">
        {/* Mobile Sidebar Overlay */}
        {mobileSidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
        )}

        {/* Sidebar - Desktop */}
        <div className="hidden lg:block">
          <Sidebar defaultCollapsed={sidebarCollapsed} />
        </div>

        {/* Sidebar - Mobile */}
        <div
          className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 lg:hidden ${
            mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <Sidebar />
        </div>

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header
            user={{
              id: user.id,
              full_name: user.full_name || user.email,
              email: user.email,
              avatar_url: user.avatar_url,
            }}
            onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
            onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
          />

          <main className="flex-1 overflow-y-auto overflow-x-hidden bg-background">
            <div className="container mx-auto p-4 lg:p-6 max-w-[1600px]">
              {children}
            </div>
          </main>
        </div>
      </div>

      <Toaster richColors position="top-right" />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
