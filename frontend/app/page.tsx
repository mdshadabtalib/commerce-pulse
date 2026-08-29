import Link from 'next/link';
import {
  ArrowRight,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Database,
  Zap,
  Shield,
  Check,
  ChevronRight,
  Sparkles,
  LineChart,
  Users,
  Package,
  Globe,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const features = [
  {
    icon: BarChart3,
    title: 'Real-Time Dashboards',
    description:
      'Monitor your entire commerce operation with live, interactive dashboards that update in real time.',
  },
  {
    icon: TrendingUp,
    title: 'AI Demand Forecasting',
    description:
      'Predict future sales with ML models trained on your historical data, seasonality, and trends.',
  },
  {
    icon: AlertTriangle,
    title: 'Anomaly Detection',
    description:
      'Catch unexpected spikes, dips, and suspicious patterns before they impact your bottom line.',
  },
  {
    icon: Database,
    title: 'Unified Data Source',
    description:
      'Connect Shopify, WooCommerce, Amazon, Stripe, and more into a single source of truth.',
  },
  {
    icon: LineChart,
    title: 'Customer Analytics',
    description:
      'Understand cohorts, churn, LTV, and purchase patterns to optimize marketing spend.',
  },
  {
    icon: Package,
    title: 'Inventory Intelligence',
    description:
      'Optimize stock levels with intelligent reorder points and SKU-level demand signals.',
  },
  {
    icon: Zap,
    title: 'Lightning Fast Reports',
    description:
      'Generate and schedule beautiful reports in seconds — exportable to PDF, CSV, and Excel.',
  },
  {
    icon: Shield,
    title: 'Enterprise-Grade Security',
    description:
      'SOC 2 Type II compliant, SOC 2 audit-ready, with role-based access and SSO support.',
  },
];

const pricingPlans = [
  {
    name: 'Starter',
    monthlyPrice: 49,
    annualPrice: 470,
    description: 'Perfect for new sellers and small operations.',
    features: [
      '1 organization',
      'Up to 10,000 orders/month',
      'Basic dashboards & reports',
      'Email support',
      '7-day data retention',
      '2 team members',
    ],
    cta: 'Start Free Trial',
    highlight: false,
  },
  {
    name: 'Growth',
    monthlyPrice: 149,
    annualPrice: 1430,
    description: 'For scaling brands that need advanced analytics.',
    features: [
      'Everything in Starter',
      'Up to 100,000 orders/month',
      'AI demand forecasting',
      'Anomaly detection',
      'Inventory intelligence',
      'Priority support',
      '15 team members',
      '90-day data retention',
      'Custom report builder',
    ],
    cta: 'Start Free Trial',
    highlight: true,
  },
  {
    name: 'Enterprise',
    monthlyPrice: null,
    annualPrice: null,
    description: 'Custom deployments with dedicated support.',
    features: [
      'Everything in Growth',
      'Unlimited orders & data',
      'Unlimited team members',
      'SSO & SAML',
      'Dedicated success manager',
      'Custom model training',
      'SLA-backed uptime',
      'On-prem deployment option',
      'Audit logs & compliance',
    ],
    cta: 'Contact Sales',
    highlight: false,
  },
];

const stats = [
  { value: '12K+', label: 'Active Brands' },
  { value: '$2.4B', label: 'GMV Analyzed' },
  { value: '99.99%', label: 'Uptime SLA' },
  { value: '40+', label: 'Integrations' },
];

const navItems = [
  { label: 'Features', href: '#features' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'Integrations', href: '#integrations' },
  { label: 'Docs', href: '/docs' },
];

export default function HomePage() {
  return (
    <div className="relative flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-lg">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Sparkles className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              {process.env.NEXT_PUBLIC_APP_NAME || 'CommercePulse'}
            </span>
          </div>
          <nav className="hidden items-center gap-8 md:flex">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/login">Sign in</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/register">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-radial pointer-events-none" />
          <div className="container relative py-24 lg:py-32">
            <div className="mx-auto flex max-w-4xl flex-col items-center text-center">
              <Badge
                variant="secondary"
                className="mb-6 gap-2 px-4 py-1.5 text-sm"
              >
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>Now with GPT-powered insight summaries</span>
              </Badge>
              <h1 className="text-balance font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl">
                The{' '}
                <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
                  AI operating system
                </span>{' '}
                for e-commerce
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground text-balance">
                Unify sales, customers, inventory, and marketing data. Forecast
                demand with ML, detect anomalies in real time, and grow revenue
                with confidence.
              </p>
              <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
                <Button size="lg" asChild className="px-8">
                  <Link href="/register">
                    Start free trial
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="px-8">
                  <Link href="#features">
                    Explore features
                  </Link>
                </Button>
              </div>
              <p className="mt-6 text-sm text-muted-foreground">
                No credit card required • 14-day free trial • Cancel anytime
              </p>
            </div>

            {/* Stats Row */}
            <div className="mx-auto mt-20 grid max-w-4xl grid-cols-2 gap-8 border-t border-border/50 pt-12 sm:grid-cols-4">
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="flex flex-col items-center text-center"
                >
                  <div className="text-3xl font-bold tracking-tight sm:text-4xl">
                    {stat.value}
                  </div>
                  <div className="mt-2 text-sm text-muted-foreground">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Integrations Bar */}
        <section
          id="integrations"
          className="border-y border-border/50 bg-muted/30 py-12"
        >
          <div className="container">
            <p className="mb-8 text-center text-sm font-medium uppercase tracking-wider text-muted-foreground">
              Trusted integrations with the tools you already use
            </p>
            <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6">
              {['Shopify', 'WooCommerce', 'Amazon', 'Stripe', 'Shopee', 'Lazada', 'BigCommerce', 'Magento'].map((brand) => (
                <div
                  key={brand}
                  className="flex items-center gap-2 text-lg font-semibold text-muted-foreground/70 hover:text-foreground transition-colors"
                >
                  <Globe className="h-5 w-5" />
                  {brand}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="container py-24 lg:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance font-bold tracking-tight">
              Everything you need to run a data-driven commerce operation
            </h2>
            <p className="mt-6 text-lg text-muted-foreground">
              One platform to unify your data, automate insights, and accelerate
              growth — no data team required.
            </p>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card
                  key={feature.title}
                  className="card-hover group relative overflow-hidden p-6 border-border/60"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-6 text-xl font-semibold">
                    {feature.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">
                    {feature.description}
                  </p>
                </Card>
              );
            })}
          </div>
        </section>

        {/* Feature Spotlight */}
        <section className="border-t border-border/50 bg-muted/20">
          <div className="container grid py-24 lg:grid-cols-2 lg:gap-12 lg:py-32 items-center">
            <div>
              <Badge variant="outline" className="mb-4">
                <TrendingUp className="mr-2 h-3.5 w-3.5" />
                AI Forecast Engine
              </Badge>
              <h2 className="text-balance font-bold tracking-tight">
                Stop guessing. Start forecasting.
              </h2>
              <p className="mt-6 text-lg leading-8 text-muted-foreground">
                Our proprietary demand models ingest years of historical data,
                seasonality, promotions, and external signals to predict future
                sales with industry-leading accuracy.
              </p>
              <ul className="mt-8 space-y-4">
                {[
                  'SKU-level predictions up to 180 days out',
                  'Confidence intervals & scenario modeling',
                  'Promotion uplift simulation',
                  'Automatic model retraining every 24h',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-5 w-5 flex-none items-center justify-center rounded-full bg-primary/10 text-primary">
                      <Check className="h-3 w-3" />
                    </div>
                    <span className="text-base">{item}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-10">
                <Button asChild variant="outline" size="lg">
                  <Link href="/register">
                    See it in action
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
              </div>
            </div>
            <div className="mt-12 lg:mt-0">
              <Card className="overflow-hidden border-border/60 shadow-2xl">
                <div className="aspect-[4/3] bg-gradient-to-br from-primary/5 via-accent to-muted p-8 flex items-center justify-center">
                  <div className="w-full space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-muted-foreground">Revenue Forecast</div>
                        <div className="text-3xl font-bold">$842,190</div>
                        <div className="mt-1 flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400">
                          <TrendingUp className="h-4 w-4" />
                          +12.4% vs last period
                        </div>
                      </div>
                      <Badge variant="secondary">95% CI</Badge>
                    </div>
                    <div className="h-40 w-full rounded-lg bg-background border border-border flex items-end gap-1 p-4">
                      {[40, 65, 45, 70, 55, 80, 60, 90, 75, 95, 85, 100].map((h, i) => (
                        <div
                          key={i}
                          className="flex-1 rounded-t bg-gradient-to-t from-primary/40 to-primary"
                          style={{ height: `${h}%` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="container py-24 lg:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance font-bold tracking-tight">
              Simple, transparent pricing
            </h2>
            <p className="mt-6 text-lg text-muted-foreground">
              Scale with your business. No hidden fees, no surprises.
            </p>
          </div>

          <div className="mx-auto mt-16 grid max-w-6xl gap-8 lg:grid-cols-3">
            {pricingPlans.map((plan) => (
              <Card
                key={plan.name}
                className={`relative flex flex-col p-8 border-border/60 ${
                  plan.highlight
                    ? 'border-primary/60 shadow-xl ring-1 ring-primary/20 scale-[1.02]'
                    : ''
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <Badge className="px-4 py-1.5 shadow-md">
                      Most Popular
                    </Badge>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-bold">{plan.name}</h3>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {plan.description}
                </p>
                <div className="mt-8">
                  {plan.monthlyPrice !== null ? (
                    <>
                      <div className="flex items-baseline gap-1">
                        <span className="text-5xl font-extrabold tracking-tight">
                          ${plan.monthlyPrice}
                        </span>
                        <span className="text-lg text-muted-foreground">
                          /month
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">
                        or ${plan.annualPrice} billed annually (20% off)
                      </p>
                    </>
                  ) : (
                    <div className="text-5xl font-extrabold tracking-tight">
                      Custom
                    </div>
                  )}
                </div>
                <Button
                  className="mt-8 w-full"
                  variant={plan.highlight ? 'default' : 'outline'}
                  size="lg"
                  asChild
                >
                  <Link href="/register">{plan.cta}</Link>
                </Button>
                <div className="mt-8 h-px w-full bg-border" />
                <ul className="mt-8 space-y-4 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-5 w-5 flex-none items-center justify-center rounded-full bg-primary/10 text-primary">
                        <Check className="h-3 w-3" />
                      </div>
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="border-t border-border/50 bg-gradient-slate">
          <div className="container py-24 lg:py-32">
            <div className="mx-auto max-w-3xl rounded-3xl border border-border/60 bg-background p-12 text-center shadow-xl lg:p-16">
              <h2 className="text-balance font-bold tracking-tight">
                Ready to pulse-check your commerce business?
              </h2>
              <p className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground">
                Join 12,000+ brands using CommercePulse to make smarter,
                faster, data-backed decisions.
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Button size="lg" asChild className="px-8">
                  <Link href="/register">
                    Start your free trial
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="px-8">
                  <Link href="/contact">Talk to sales</Link>
                </Button>
              </div>
              <p className="mt-6 text-sm text-muted-foreground">
                Setup takes under 2 minutes • Fully onboarded in a week
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 bg-background">
        <div className="container py-16">
          <div className="grid gap-12 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                  <Sparkles className="h-5 w-5" />
                </div>
                <span className="text-lg font-bold tracking-tight">
                  {process.env.NEXT_PUBLIC_APP_NAME || 'CommercePulse'}
                </span>
              </div>
              <p className="mt-4 max-w-xs text-sm text-muted-foreground">
                The AI-powered commerce analytics platform built for modern
                brands.
              </p>
              <div className="mt-6 flex gap-4">
                {['Twitter', 'LinkedIn', 'GitHub'].map((social) => (
                  <Link
                    key={social}
                    href="#"
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {social}
                  </Link>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold">Product</h4>
              <ul className="mt-4 space-y-3">
                {['Features', 'Pricing', 'Integrations', 'Changelog', 'Roadmap'].map((item) => (
                  <li key={item}>
                    <Link
                      href="#"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold">Resources</h4>
              <ul className="mt-4 space-y-3">
                {['Documentation', 'API Reference', 'Guides', 'Blog', 'Help Center'].map((item) => (
                  <li key={item}>
                    <Link
                      href="#"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold">Company</h4>
              <ul className="mt-4 space-y-3">
                {['About', 'Careers', 'Press', 'Contact', 'Partners'].map((item) => (
                  <li key={item}>
                    <Link
                      href="#"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="mt-16 flex flex-col items-center justify-between gap-4 border-t border-border/50 pt-8 sm:flex-row">
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} {process.env.NEXT_PUBLIC_APP_NAME || 'CommercePulse'}, Inc. All rights reserved.
            </p>
            <div className="flex gap-6">
              {['Privacy', 'Terms', 'Security', 'Status'].map((item) => (
                <Link
                  key={item}
                  href="#"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  {item}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
