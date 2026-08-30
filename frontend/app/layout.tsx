import type { Metadata, Viewport } from 'next';
import { ThemeProvider } from 'next-themes';
import { Toaster } from 'sonner';
import { QueryProvider } from '@/components/providers/query-provider';
import './globals.css';

const appName = process.env.NEXT_PUBLIC_APP_NAME || 'CommercePulse';
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: `${appName} - AI-Powered Commerce Analytics`,
    template: `%s | ${appName}`,
  },
  description:
    'CommercePulse is the all-in-one AI-powered analytics platform for e-commerce businesses. Track sales, forecast demand, detect anomalies, and unlock actionable insights.',
  keywords: [
    'ecommerce analytics',
    'sales dashboard',
    'demand forecasting',
    'anomaly detection',
    'business intelligence',
    'commerce analytics',
    'AI analytics',
  ],
  authors: [
    {
      name: 'CommercePulse',
    },
  ],
  creator: 'CommercePulse',
  publisher: 'CommercePulse',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: siteUrl,
    siteName: appName,
    title: `${appName} - AI-Powered Commerce Analytics`,
    description:
      'CommercePulse is the all-in-one AI-powered analytics platform for e-commerce businesses. Track sales, forecast demand, detect anomalies, and unlock actionable insights.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: `${appName} - AI-Powered Commerce Analytics`,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: `${appName} - AI-Powered Commerce Analytics`,
    description:
      'CommercePulse is the all-in-one AI-powered analytics platform for e-commerce businesses. Track sales, forecast demand, detect anomalies, and unlock actionable insights.',
    images: ['/og-image.png'],
    creator: '@commercepulse',
  },
  icons: {
    icon: [
      {
        url: '/favicon.ico',
        sizes: 'any',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: [
      {
        url: '/apple-icon.png',
      },
    ],
  },
  manifest: '/site.webmanifest',
  category: 'business',
  alternates: {
    canonical: siteUrl,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'hsl(0 0% 100%)' },
    { media: '(prefers-color-scheme: dark)', color: 'hsl(222.2 84% 4.9%)' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  minimumScale: 1,
  viewportFit: 'cover',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
    >
      <body
        className="min-h-screen bg-background text-foreground antialiased"
        suppressHydrationWarning
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            {children}
            <Toaster
              position="top-right"
              richColors
              closeButton
              toastOptions={{
                duration: 5000,
                style: {
                  borderRadius: '0.75rem',
                  border: '1px solid hsl(var(--border))',
                  background: 'hsl(var(--background))',
                },
              }}
            />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
