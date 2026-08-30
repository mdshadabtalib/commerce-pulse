'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Package,
  DollarSign,
  TrendingUp,
  AlertCircle,
  Search,
  Filter,
  Download,
} from 'lucide-react';

import { formatCurrency, formatCompactNumber } from '@/lib/utils';
import { KPICard } from '@/components/dashboard/kpi-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ProductResponse } from '@/types';

export default function ProductsPage() {
  const [searchTerm, setSearchTerm] = React.useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['products', 'list', searchTerm],
    queryFn: async () => {
      return {
        kpis: {
          total_products: 1248,
          active_products: 1142,
          total_revenue: 847250.75,
          avg_product_revenue: 741.35,
        },
        products: [
          {
            id: '1',
            title: 'Wireless Bluetooth Headphones',
            sku: 'WBH-001',
            status: 'active' as const,
            product_type: 'Electronics',
            vendor: 'AudioTech',
            image_url: null,
            tags: ['audio', 'wireless', 'bluetooth'],
            source: 'shopify' as const,
            total_revenue: 45800,
            total_orders: 183,
            total_quantity_sold: 224,
            units_in_stock: 156,
            average_order_value: 250.27,
            growth_rate: 0.15,
          },
          {
            id: '2',
            title: 'Organic Cotton T-Shirt - Classic',
            sku: 'OCT-CLS-BLK',
            status: 'active' as const,
            product_type: 'Clothing',
            vendor: 'EcoWear',
            image_url: null,
            tags: ['clothing', 'organic', 'basics'],
            source: 'shopify' as const,
            total_revenue: 12450,
            total_orders: 498,
            total_quantity_sold: 645,
            units_in_stock: 2134,
            average_order_value: 25.00,
            growth_rate: 0.08,
          },
          {
            id: '3',
            title: 'Premium Yoga Mat - Pro Series',
            sku: 'YM-PRO-001',
            status: 'active' as const,
            product_type: 'Sports & Fitness',
            vendor: 'ZenFit',
            image_url: null,
            tags: ['fitness', 'yoga', 'premium'],
            source: 'woocommerce' as const,
            total_revenue: 18900,
            total_orders: 270,
            total_quantity_sold: 285,
            units_in_stock: 89,
            average_order_value: 70.00,
            growth_rate: 0.22,
          },
        ] as ProductResponse[],
      };
    },
  });

  const kpis = data?.kpis;
  const products = data?.products || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Products</h1>
          <p className="text-muted-foreground mt-1">
            Manage inventory and track product performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Filter className="mr-2 h-4 w-4" />
            Filters
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Products"
          value={formatCompactNumber(kpis?.total_products || 0)}
          icon={Package}
          loading={isLoading}
        />
        <KPICard
          title="Active Products"
          value={formatCompactNumber(kpis?.active_products || 0)}
          icon={TrendingUp}
          loading={isLoading}
        />
        <KPICard
          title="Total Revenue"
          value={formatCurrency(kpis?.total_revenue || 0)}
          icon={DollarSign}
          loading={isLoading}
        />
        <KPICard
          title="Avg Product Revenue"
          value={formatCurrency(kpis?.avg_product_revenue || 0)}
          icon={DollarSign}
          loading={isLoading}
        />
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Product Catalog</CardTitle>
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-[400px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border text-left text-sm text-muted-foreground">
                    <th className="pb-3 font-medium">Product</th>
                    <th className="pb-3 font-medium">SKU</th>
                    <th className="pb-3 font-medium">Stock</th>
                    <th className="pb-3 font-medium text-right">Orders</th>
                    <th className="pb-3 font-medium text-right">Revenue</th>
                    <th className="pb-3 font-medium text-right">Growth</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => (
                    <tr key={product.id} className="border-b border-border/50 last:border-0 hover:bg-muted/50 transition-colors">
                      <td className="py-4">
                        <div className="font-medium">{product.title}</div>
                        <div className="text-sm text-muted-foreground">{product.product_type}</div>
                      </td>
                      <td className="py-4">
                        <code className="text-xs bg-muted px-2 py-1 rounded">{product.sku}</code>
                      </td>
                      <td className="py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{product.units_in_stock}</span>
                          {product.units_in_stock && product.units_in_stock < 100 && (
                            <AlertCircle className="h-4 w-4 text-warning" />
                          )}
                        </div>
                      </td>
                      <td className="py-4 text-right">{product.total_orders}</td>
                      <td className="py-4 text-right font-medium">{formatCurrency(product.total_revenue)}</td>
                      <td className="py-4 text-right">
                        {product.growth_rate != null && (
                          <Badge variant={product.growth_rate > 0 ? 'success' : 'destructive'} size="sm">
                            {product.growth_rate > 0 ? '+' : ''}{(product.growth_rate * 100).toFixed(1)}%
                          </Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
