import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Authentication - CommercePulse',
  description: 'Sign in to your CommercePulse account',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
