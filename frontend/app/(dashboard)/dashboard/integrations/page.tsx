'use client';

import * as React from 'react';
import { Plug, Check, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  connected: boolean;
  status: 'active' | 'error' | 'disconnected';
  lastSync?: string;
}

const mockIntegrations: Integration[] = [
  {
    id: '1',
    name: 'Shopify',
    description: 'Connect your Shopify store to sync orders, customers, and products',
    icon: '🛍️',
    connected: true,
    status: 'active',
    lastSync: '5 minutes ago',
  },
  {
    id: '2',
    name: 'WooCommerce',
    description: 'Import data from your WordPress WooCommerce store',
    icon: '🛒',
    connected: false,
    status: 'disconnected',
  },
  {
    id: '3',
    name: 'Stripe',
    description: 'Sync payment data and transaction history from Stripe',
    icon: '💳',
    connected: true,
    status: 'active',
    lastSync: '1 hour ago',
  },
  {
    id: '4',
    name: 'Amazon Seller Central',
    description: 'Import orders and inventory from Amazon marketplace',
    icon: '📦',
    connected: false,
    status: 'disconnected',
  },
  {
    id: '5',
    name: 'Google Analytics',
    description: 'Connect Google Analytics for enhanced traffic insights',
    icon: '📊',
    connected: true,
    status: 'error',
    lastSync: '3 days ago',
  },
  {
    id: '6',
    name: 'Mailchimp',
    description: 'Sync customer data with your Mailchimp campaigns',
    icon: '📧',
    connected: false,
    status: 'disconnected',
  },
];

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = React.useState(mockIntegrations);

  const toggleConnection = (id: string) => {
    setIntegrations(prev =>
      prev.map(integration =>
        integration.id === id
          ? {
              ...integration,
              connected: !integration.connected,
              status: !integration.connected ? 'active' : 'disconnected',
            }
          : integration
      )
    );
  };

  const connectedCount = integrations.filter(i => i.connected).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Integrations</h1>
          <p className="text-muted-foreground mt-1">
            Connect your favorite tools and platforms
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">
            {connectedCount} Connected
          </Badge>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Integrations</p>
                <p className="text-2xl font-bold">{integrations.length}</p>
              </div>
              <Plug className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active</p>
                <p className="text-2xl font-bold text-green-500">{connectedCount}</p>
              </div>
              <Check className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Issues</p>
                <p className="text-2xl font-bold text-amber-500">
                  {integrations.filter(i => i.status === 'error').length}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Integrations Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {integrations.map((integration) => (
          <Card key={integration.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-4xl">{integration.icon}</div>
                  <div>
                    <CardTitle className="text-lg">{integration.name}</CardTitle>
                    <CardDescription>{integration.description}</CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Status */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {integration.status === 'active' && (
                      <>
                        <Check className="h-4 w-4 text-green-500" />
                        <span className="text-sm text-green-500">Connected</span>
                      </>
                    )}
                    {integration.status === 'error' && (
                      <>
                        <AlertCircle className="h-4 w-4 text-amber-500" />
                        <span className="text-sm text-amber-500">Error</span>
                      </>
                    )}
                    {integration.status === 'disconnected' && (
                      <span className="text-sm text-muted-foreground">Not connected</span>
                    )}
                  </div>
                  {integration.lastSync && (
                    <span className="text-xs text-muted-foreground">
                      Last sync: {integration.lastSync}
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id={`toggle-${integration.id}`}
                      checked={integration.connected}
                      onCheckedChange={() => toggleConnection(integration.id)}
                    />
                    <Label htmlFor={`toggle-${integration.id}`} className="text-sm">
                      {integration.connected ? 'Enabled' : 'Disabled'}
                    </Label>
                  </div>
                  {integration.connected ? (
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        Configure
                      </Button>
                      {integration.status === 'error' && (
                        <Button variant="outline" size="sm">
                          Reconnect
                        </Button>
                      )}
                    </div>
                  ) : (
                    <Button size="sm">
                      Connect
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Help Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="rounded-full bg-primary/10 p-2">
              <Plug className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">Need help with integrations?</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Check our documentation or contact support for assistance with connecting your tools
              </p>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" size="sm">
                  View Documentation
                </Button>
                <Button variant="outline" size="sm">
                  Contact Support
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
